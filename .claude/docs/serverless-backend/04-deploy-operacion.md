# 04 — Deploy y operacion

> [<- 03-datos](03-datos.md) | [README](README.md)

Como deployar el backend (recursos compartidos + Lambdas), los comandos
devtools, rotar secrets y troubleshooting. devtools provisiona cada
recurso con AWS CLI directo y mantiene el estado en archivos locales —
sin SAM ni CloudFormation. Todo se opera con
`python devtools/run.py serverless <command>`.

## 1. Pre-requisitos

| Herramienta | Version min | Verificar |
|-------------|-------------|-----------|
| AWS CLI | 2.15+ | `aws --version` |
| Docker | reciente (opcional, para `run --stage=local` en modo RIE) | `docker --version` |
| Python | 3.13+ | `python3 --version` |
| uv | 0.5+ | `uv --version` |
| psql | 16+ (opcional, para sesiones interactivas contra Neon) | `psql --version` |
| neonctl | reciente (opcional, gestionar branches Neon) | `neon --version` |
| jq, curl | recientes | — |

Setup inicial del modulo:

```bash
python devtools/run.py serverless init    # uv sync + verifica AWS CLI + uv
```

## 2. Setup AWS (una vez por cuenta)

### 2.1. Profile SSO

El backend del portfolio vive en la cuenta AWS `637423614564`, accesible
con el perfil `tfs-dev` (SSO start URL `https://tfs-tech.awsapps.com/start`,
role `AdministratorAccess`).

```bash
aws configure sso
# SSO start URL, region us-east-1, role AdministratorAccess, profile tfs-dev
aws sts get-caller-identity --profile tfs-dev
```

> **CRITICO — el perfil AWS de los comandos `serverless`.** Los comandos
> `deploy`, `destroy`, `status`, `provision-infra` y `run` (contra un
> stage provisionado) ejecutan `aws` por debajo. Por defecto usan el
> perfil del shell (`AWS_PROFILE` o `[default]`), que puede apuntar a
> OTRA cuenta (ej. un perfil de otro proyecto) o tener el token SSO
> expirado. Por eso estos comandos aceptan `--aws-profile=tfs-dev`:
> inyecta `--profile tfs-dev` en los comandos `aws` y garantiza que se
> opera sobre la cuenta del portfolio.
>
> SIEMPRE pasar `--aws-profile=tfs-dev` (o `export AWS_PROFILE=tfs-dev`
> en la sesion de trabajo del portfolio). Sin esto, un
> `aws sso login --profile tfs-dev` refresca el perfil equivocado y el
> comando sigue fallando con `Error when retrieving token from sso`.

### 2.2. KMS key para los SSM SecureString

```bash
aws kms create-key --profile tfs-dev --region us-east-1 \
  --description "SSM Parameters del portfolio backend"
aws kms create-alias --profile tfs-dev --region us-east-1 \
  --alias-name alias/portfolio-lambdas --target-key-id <KEY_ID>
```

### 2.3. Cargar los secrets a SSM

Via devtools (crea el parametro como `SecureString` cifrado con la KMS
key del proyecto):

```bash
python devtools/run.py serverless setup-ssm --name=/portfolio/turnstile-secret
python devtools/run.py serverless setup-ssm --name=/portfolio/dev/neon-url
```

Inventario completo de SSM Parameters (paths por stage, quien los lee):
[.claude/rules/serverless-secrets.md](../../rules/serverless-secrets.md).

### 2.4. Servicios externos

- **Cloudflare Turnstile**: widget en mode Managed con los 6 hostnames
  del portfolio. Detalle: skill `cloudflare-turnstile`.
- **Neon**: proyecto serverless en `us-east-1`, PostgreSQL 18, branches
  por stage. Detalle: [.claude/rules/neon-management.md](../../rules/neon-management.md).
- **AWS SES**: domain identity verificada en `us-east-1`, DKIM/SPF/DMARC
  en Cloudflare DNS, production access. Detalle: skill `aws-ses`.

## 3. Deploy del backend

Los recursos compartidos van PRIMERO; los 4 Lambdas leen sus
identificadores desde SSM.

```bash
# 1. Todos los recursos compartidos (5 tablas DynamoDB + API GW + DLQ SQS)
python devtools/run.py serverless provision-infra --stage=dev --aws-profile=tfs-dev

# 2. Los 4 Lambdas (en cualquier orden entre si)
python devtools/run.py serverless deploy --lambda=db --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=contact_form --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=tracking_pixel --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=stream_processor --stage=dev --aws-profile=tfs-dev

# 3. Aplicar el schema PostgreSQL (invocando la Lambda db)
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/migrate.json --aws-profile=tfs-dev
```

`provision-infra` provisiona en orden los 7 recursos compartidos de
`serverless/lambda/resources/` con AWS CLI directo y publica sus
identificadores a SSM. `list-resources` lista los recursos declarados.

Para `stage` y `prod`: mismos comandos cambiando `--stage`. `deploy` arma
el artefacto `build.zip` del Lambda con uv (`uv pip install --target
build/`) + vendoring selectivo de `shared/`, lee el `manifest.yaml`,
carga el estado previo y aplica la accion que el diff de hashes indica
(`create` / `update-function-code` / `update-function-configuration` /
`noop`). `--dry-run` imprime las acciones sin ejecutarlas.

`deploy` y `run` regeneran el `build/` del Lambda (deps con uv +
vendoring selectivo de los subpaquetes de `serverless/lambda/shared/` que
el Lambda usa, en `build/core/shared/`) antes de ejecutar; `build/` y
`build.zip` son efimeros y se limpian al terminar.

### Estado y destroy

`status` compara el estado local contra los `describe-*` de AWS; sirve
para detectar drift. `destroy` borra los recursos de un stage en orden
inverso al de creacion (primero los Lambdas, luego los recursos
compartidos) y limpia los archivos de estado:

```bash
# Estado de un lambda (local vs AWS)
python devtools/run.py serverless status --lambda=db --stage=dev --aws-profile=tfs-dev

# Destruir TODO el backend de un stage (lambdas + infra) — requiere --yes
python devtools/run.py serverless destroy --stage=dev --yes --aws-profile=tfs-dev

# Destruir solo un lambda de un stage
python devtools/run.py serverless destroy --lambda=db --stage=dev --yes --aws-profile=tfs-dev
```

## 4. Desarrollo local

```bash
# Ejecutar el Lambda en local. --stage=local usa por defecto el Runtime
#   Interface Emulator (RIE) en un contenedor Docker; --runtime-mode=direct
#   corre el handler en proceso (sin Docker, sin AWS).
python devtools/run.py serverless run \
  --stage=local --lambda=db --event=events/current.json
python devtools/run.py serverless run \
  --stage=local --lambda=db --event=events/current.json --runtime-mode=direct

# Invocar un Lambda ya deployado (--stage=dev|stage|prod -> aws lambda invoke)
python devtools/run.py serverless run \
  --stage=dev --lambda=db --event=events/current.json --aws-profile=tfs-dev

# Tests de un Lambda (viven dentro del Lambda)
python devtools/run.py serverless tests --type=unit --lambda=db
python devtools/run.py serverless tests --type=integration --lambda=db

# Tests de la libreria comun shared/
python devtools/run.py serverless tests --type=coverage --shared
```

## 5. Inventario de comandos devtools

`python devtools/run.py serverless <command> [flags]`. Inventario
colorizado: `serverless help`.

### Lambda (modo `lambda-controller`, `--lambda` requerido)

`--lambda=<nombre>` resuelve el lambda contra
`serverless/lambda/services/<nombre>/` (forma recomendada) y valida que
la carpeta cumpla la estructura lambda-controller. Como alternativa,
`--path=<dir>` apunta a un directorio explicito (`--module` es alias de
`--path`).

| Comando | Que hace |
|---------|----------|
| `run --stage=<env>` | `--stage=local` -> RIE via Docker (o `--runtime-mode=direct`); `--stage=dev\|stage\|prod` -> `aws lambda invoke` contra el deployado |
| `deploy` | Arma `build.zip` con uv + vendoring selectivo de `shared/`, lo provisiona con AWS CLI y actualiza el estado local |
| `destroy --yes` | Borra los recursos del lambda (o de todo el stage) en orden inverso al de creacion y limpia el estado |
| `status` | Compara el estado local vs los `describe-*` de AWS (deteccion de drift) |
| `tests --type=<unit\|integration\|coverage>` | `pytest` del Lambda; sin target corre la suite completa, con `--shared` corre la libreria comun |

`deploy`, `destroy`, `status` y `run` (contra un stage deployado)
aceptan `--aws-profile=<perfil>` para fijar el perfil AWS CLI de los
comandos `aws`. Usar SIEMPRE `--aws-profile=tfs-dev` (ver seccion 2.1).

### Infra / recursos

| Comando | Que hace |
|---------|----------|
| `provision-infra` | Provisiona en orden TODOS los recursos de `resources/` con AWS CLI directo. Acepta `--aws-profile=tfs-dev` |
| `list-resources` | Lista los recursos declarados en `resources/` |
| `destroy --stage=<env> --yes` | Borra todo el backend del stage (lambdas + recursos compartidos) |

### Setup / mantenimiento / calidad

| Comando | Que hace |
|---------|----------|
| `init` | Setup inicial (uv sync + verifica AWS CLI + uv) |
| `clean` | Borra caches + artefactos efimeros (`build/`, `build.zip`, vendor) |
| `lint` / `lint-fix` / `format` | Ruff sobre `shared/` + `services/` |
| `typecheck` | mypy --strict |
| `tests --type=coverage --shared` | pytest + cobertura de la libreria comun `shared/` |

### Secrets / DNS

| Comando | Que hace |
|---------|----------|
| `setup-ssm` | Crear un SSM Parameter (KMS) |
| `rotate-secret` | Rotar el valor de un SSM Parameter |
| `verify-ses-dns` | `dig` de DKIM/SPF/DMARC contra Cloudflare |
| `request-ses-prod` | Plantilla del ticket de SES production access |

### Database (Neon)

Los comandos `db-*` dedicados se eliminaron. La DB se opera invocando la
Lambda `db` con `serverless run`; cada `command` tiene su event en
`serverless/lambda/services/db/events/`:

| Operacion | Comando |
|-----------|---------|
| Aplicar migraciones Alembic | `run --stage=<env> --lambda=db --event=events/migrate.json` |
| Rollback de migracion (DESTRUCTIVO) | `run --stage=<env> --lambda=db --event=events/downgrade.json` |
| Revision Alembic aplicada | `run --stage=<env> --lambda=db --event=events/current.json` |
| Historial de migraciones | `run --stage=<env> --lambda=db --event=events/show_migrations.json` |
| Adoptar el schema existente | `run --stage=<env> --lambda=db --event=events/stamp.json` |
| Listar tablas + row counts | `run --stage=<env> --lambda=db --event=events/tables.json` |
| Cargar datos del CV (seed) | `run --stage=<env> --lambda=db --event=events/seed.json` |

Para una sesion `psql` interactiva contra Neon, usar `psql` directo. Para
gestionar branches de Neon, usar `neonctl`. Ver
[.claude/rules/neon-management.md](../../rules/neon-management.md).

### Observability / rate-limit

| Comando | Que hace |
|---------|----------|
| `metrics` | Resumen CloudWatch (Lambda + API GW) |
| `alarms` | Lista alarmas + estado |
| `rate-limit <sub-accion>` | Gestion de `rate-limit-rules`/`-buckets`: `list`, `show`, `set`, `allow`, `block`, `unblock`, `stats`, `clear-buckets` |

> No hay SAM ni CloudFormation: devtools provisiona cada recurso con AWS
> CLI directo y registra lo creado en un archivo de estado local
> (`serverless/lambda/.state/<scope>-<stage>.json`). Detalle del estado:
> [05-estado-local.md](05-estado-local.md).

## 6. Rotar secrets

### Turnstile secret

```bash
python devtools/run.py serverless rotate-secret \
  --name=/portfolio/turnstile-secret --confirm
```

El Lambda `contact_form` lee el secret de SSM y lo cachea con
`shared/cache` (TTL 300s); tras la rotacion el valor nuevo entra al
expirar el cache o en el siguiente cold start. Si la rotacion regenera
el widget, actualizar tambien la sitekey publica en el frontend.

### Neon connection URL

```bash
# 1. Regenerar el password en la consola Neon -> Roles
# 2. Actualizar el SSM Parameter del stage
python devtools/run.py serverless rotate-secret \
  --name=/portfolio/dev/neon-url --confirm
# 3. Revocar el credential viejo en Neon tras validar
```

`stream_processor` y `db` releen la URL en el siguiente cold start.

## 7. Troubleshooting

| Sintoma | Causa probable | Solucion |
|---------|----------------|----------|
| `Error when retrieving token from sso` aunque hiciste `aws sso login` | El comando usa el perfil del shell (`AWS_PROFILE`/`[default]`), no `tfs-dev` — refrescaste el perfil equivocado | Pasar `--aws-profile=tfs-dev` al comando `serverless` (o `export AWS_PROFILE=tfs-dev`). Ver seccion 2.1 |
| `UnauthorizedOperation` en el deploy | Token SSO de `tfs-dev` expirado | `aws sso login --profile tfs-dev` + `--aws-profile=tfs-dev` |
| `Parameter ... not found` al deployar un Lambda | El recurso compartido no esta provisionado en ese stage (el SSM param no existe) | `provision-infra --stage=<stage>` primero |
| El Lambda falla en runtime con `Parameter ... not found` | El path SSM del nombre de tabla no existe — recurso no provisionado | Provisionar el recurso compartido correspondiente |
| `deploy` fallo a mitad y dejo recursos parciales | Sin rollback transaccional; el estado local registra lo creado | Re-ejecutar `deploy` (es idempotente) o `destroy --lambda=<X>` + `deploy` |
| El estado local no coincide con AWS (drift) | Alguien edito un recurso a mano en la consola | `serverless status` para ver la diferencia; re-deployar o destruir+recrear |
| `ImportModuleError` / `No module named 'shared'` | Subpaquete de `shared/` no vendorizado en `build/core/shared/` (el AST scan no detecto el import) | Verificar que el import es `from shared.<sub>...` explicito; redeployar (devtools regenera `build/` en cada `deploy`) — no editar `build/` a mano |
| `POST /contact` responde 502 | Lambda timeout o env var faltante | Revisar logs del Lambda en CloudWatch; `serverless metrics --stage=<stage>` |
| `POST /track` responde 400 | Body invalido segun el JSON Schema / Pydantic | Revisar el payload contra `models/` del `tracking_pixel` |
| Fila no replicada a Neon | `stream_processor` falla o Neon caido | Revisar logs del `stream_processor`; verificar `/portfolio/<stage>/neon-url`; revisar la DLQ |
| Email no llega | SES en sandbox / bounce / supresion | `verify-ses-dns`; revisar SES sending stats y la suppression list (skill `aws-ses`) |
| Costos suben sobre USD 5/mes | Hot key DynamoDB, bucle de invocaciones, bounce rate alto | AWS Cost Explorer por servicio; revisar `Invocations` y `ConsumedCapacity` |

### DLQ del stream_processor

Si la DLQ acumula mensajes: lo tipico es un schema mismatch tras una
migracion. Revisar los logs del `stream_processor`, corregir el
transformer/migracion y reprocesar. Una vez resuelto, los mensajes
viejos irrecuperables se pueden purgar (`aws sqs purge-queue`).

### Ataque DDoS sostenido

1. Confirmar via metricas de API Gateway (`Count` se dispara).
2. Bloquear las IPs origen con `serverless rate-limit block`.
3. Si el bot pool es grande, activar "Under Attack Mode" en Cloudflare.
4. Como ultimo recurso, evaluar reactivar AWS WAF temporal (~$7/mes).

## 8. Observabilidad y costos

- **Logs**: CloudWatch Logs JSON (Powertools), retention 7 dias. Son la
  fuente de verdad para troubleshooting.
- **Alarmas**: NINGUNA operacional. Solo el AWS Billing Alarm global
  (gratis). Monitoring on-demand con `serverless metrics --since=24h`.
- **Costo**: ~$0/mes — todo free tier perpetuo. Sin WAF (rate-limit con
  DynamoDB, ahorra ~$7/mes), sin alarmas, retention 7d. Ahorro total vs
  una arquitectura con WAF + alarmas + logs 30d: ~$94/ano.

## 9. Referencias

- Formato y operacion de cada Lambda (`lambda-controller`):
  [.claude/rules/lambda-controller.md](../../rules/lambda-controller.md) +
  [.claude/docs/lambda-controller/06-devtools-operations.md](../lambda-controller/06-devtools-operations.md)
- Secrets SSM: [.claude/rules/serverless-secrets.md](../../rules/serverless-secrets.md)
- Neon (migraciones, branches, rollback): [.claude/rules/neon-management.md](../../rules/neon-management.md)
- AWS: skills `aws-lambda-python`, `aws-api-gateway`, `aws-dynamodb`, `aws-ses`

---

[<- 03-datos](03-datos.md) | [README](README.md)
