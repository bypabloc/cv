# 01 — Contexto y decision

> [README](README.md) | [Siguiente: 02](02-arquitectura-objetivo.md)

## 1. Problema

El backend serverless del portfolio gestiona su infraestructura AWS con
un modelo hibrido inconsistente:

- La **infra compartida** (API Gateway, tablas DynamoDB, DLQ) se deploya
  con `aws cloudformation deploy` directo desde
  [devtools/serverless/infra_deploy.py](../../../devtools/serverless/infra_deploy.py).
- Los **4 Lambdas** dependen de **SAM CLI**: `sam deploy` y
  `sam local invoke`, alimentados por un `template.yaml` efimero que
  [devtools/serverless/sam_generate.py](../../../devtools/serverless/sam_generate.py)
  genera desde el `lambda.yaml` de cada Lambda.

Esto obliga a tener instalados **tres** CLIs (SAM + AWS + uv), mantener
una traduccion de 671 lineas (`sam_generate.py`), y trabajar contra una
capa de abstraccion que ya esta estorbando.

## 2. Estado actual: SAM ya es una capa delgada

El proyecto esta a mitad de camino de no usar SAM. Hechos verificados en
el codigo:

| Pieza | Quien la hace hoy | Usa SAM? |
|-------|-------------------|----------|
| Infra compartida (deploy) | `aws cloudformation deploy` | NO |
| Build del artefacto del Lambda | `uv pip install --target` ([packaging.py](../../../devtools/serverless/packaging.py)) | NO |
| Invocacion remota (`invoke-remote`) | `aws lambda invoke` | NO |
| Generacion del `template.yaml` | `sam_generate.py` (Transform SAM) | SI |
| Deploy del Lambda | `sam deploy --resolve-s3` | SI |
| Ejecucion local (`run-local`) | `sam local invoke` | SI |

`packaging.py` ya hace el trabajo de `sam build`: el `template.yaml`
generado NO lleva `Metadata.BuildMethod`, asi que `sam deploy` solo
zipea el `build/` que devtools ya armo con uv. **SAM aporta hoy solo
tres cosas**: (1) la macro `AWS::Serverless::Function`, (2) subir el zip
a S3 + crear/actualizar el stack CloudFormation, (3) `sam local invoke`.

## 3. Por que SAM estorba (motivacion confirmada en el codigo)

| Problema | Evidencia |
|----------|-----------|
| **Se choca con la logica de SAM al cambiar algo** | [sam_generate.py:427-447](../../../devtools/serverless/sam_generate.py#L427-L447): SAM no acepta `Fn::ImportValue` en el `RestApiId` de un `Event Api`, asi que las rutas HTTP NO se pudieron modelar con el `Event Api` de SAM — hubo que escribirlas con recursos CloudFormation nativos (`AWS::ApiGateway::Resource/Method/Deployment` + `Lambda::Permission`). El proyecto ya pelea contra SAM. |
| **Build "falso"** | `sam build` no corre: devtools ya empaqueta con uv. La capa de build de SAM es decorativa. |
| **Doble traduccion** | `lambda.yaml` -> `template.yaml` (SAM) -> CloudFormation. Dos saltos donde podria haber uno: `lambda.yaml` -> llamadas AWS. |
| **Complejidad opaca** | 671 lineas en `sam_generate.py` para emitir un YAML que SAM re-expande server-side. El rol IAM real y el LogGroup no son visibles hasta que el stack existe. |
| **Tres binarios** | SAM CLI (pesado, Python propio) ademas de AWS CLI + uv. |

## 4. Que aporta SAM (lo que se pierde)

Honestidad sobre el costo de eliminarlo:

| Ventaja de SAM | Peso en este proyecto |
|----------------|----------------------|
| **CloudFormation: estado declarativo** | Rollback automatico en fallo de deploy, drift detection, `delete-stack` borra todo. Es lo mas valioso que se pierde. |
| Macro `AWS::Serverless::Function` | Expande 1 recurso en ~5 (Function + Role + LogGroup + Permissions + EventSourceMapping). Ahorra ~150 lineas de wiring por Lambda. |
| `sam local invoke` | Corre el Lambda en un contenedor identico al runtime AWS. |
| `--resolve-s3` | Gestiona el bucket de artefactos solo. |

## 5. Decision

**Eliminar SAM y CloudFormation por completo.** devtools gestiona cada
recurso AWS con AWS CLI imperativo. Lo que CloudFormation daba gratis
(estado, orden de dependencias, idempotencia) se reimplementa de forma
minima y explicita en devtools.

### Justificacion

1. **El proyecto ya va en esa direccion.** La infra compartida y el
   build ya no usan SAM. Eliminar SAM del deploy de Lambdas cierra la
   inconsistencia, no abre una nueva.
2. **Control y transparencia.** Cada cambio de infra es una llamada AWS
   CLI explicita y editable, no una macro server-side. Se ve exactamente
   que rol, que politica, que LogGroup se crea.
3. **Un solo modelo mental.** `manifest.yaml` + `resources/*.yaml` ->
   `provisioner` -> AWS CLI. Sin la doble traduccion ni el
   `template.yaml` efimero. (El manifiesto `lambda.yaml` de cada Lambda
   se renombra a `manifest.yaml` como parte de la migracion — ver
   [04-fase-2-provisioner-lambda.md](04-fase-2-provisioner-lambda.md).)
4. **Menos dependencias.** Se elimina SAM CLI. Quedan AWS CLI + uv.
5. **El costo del estado declarativo es asumible para este proyecto.**
   La infra es chica (4 Lambdas + ~7 recursos compartidos) y la data es
   descartable. No se necesita el rollback transaccional de
   CloudFormation; basta un comando idempotente re-ejecutable.

### Lo que reemplaza a cada pieza de SAM

| Pieza SAM | Reemplazo |
|-----------|-----------|
| `Transform: AWS::Serverless` (macro) | `provisioner.py` expande explicitamente: `aws iam create-role` + `attach-role-policy`, `aws lambda create-function`, `aws logs create-log-group`, `aws lambda create-event-source-mapping`, `aws lambda add-permission` |
| `sam deploy` (zip -> S3 -> CFN) | `aws s3 cp build.zip s3://...` + `aws lambda create-function` / `update-function-code` |
| `sam local invoke` | AWS Lambda RIE (Runtime Interface Emulator) via Docker, con fallback a ejecucion directa del handler |
| Estado / rollback de CloudFormation | Archivo de estado en devtools: `serverless/lambda/.state/<scope>-<stage>.json` con ARNs + hash de config aplicada |
| `aws cloudformation deploy` de la infra | `infra_provision.py` crea las tablas / API / DLQ con AWS CLI directo |

## 6. Trade-offs aceptados (riesgos conocidos)

- **Sin rollback transaccional.** Si `deploy` falla a mitad, devtools
  deja recursos parciales. Mitigacion: el estado registra que se creo y
  el comando es idempotente re-ejecutable (AC-8 en
  [04](04-fase-2-provisioner-lambda.md)).
- **Sin drift detection nativo.** Si alguien cambia un recurso a mano en
  la consola AWS, devtools no lo detecta automaticamente. Mitigacion:
  comando `serverless status` que compara estado local vs `describe-*`.
- **Orden de dependencias manual.** Lo que CloudFormation resolvia por
  grafo, devtools lo hace en orden fijo (crear) y orden inverso
  (destruir). Documentado y testeado.
- **`provisioner.py` + `state.py` cargan complejidad.** Es complejidad
  explicita y editable a cambio de la complejidad opaca de SAM —
  exactamente el objetivo. Neto positivo porque ya se mantenia
  `sam_generate.py`.

## 7. Alcance

- **Incluye**: los 4 Lambdas (`contact_form`, `tracking_pixel`,
  `stream_processor`, `db`), la infra compartida (`resources/`), el CLI
  de devtools, las rules / docs / skill.
- **No incluye**: cambios en el codigo de runtime de los Lambdas
  (`core/`), ni en el schema de DB, ni en el frontend Astro.
- **Migracion de infra viva**: recrear desde cero. Se destruyen los
  stacks CloudFormation `portfolio-infra-*` y `portfolio-<lambda>-*` en
  dev / stage / prod y se reaprovisiona con devtools. La data de
  DynamoDB es descartable (confirmado).

---

[README](README.md) | [Siguiente: 02](02-arquitectura-objetivo.md)
