# 04 — Deploy y operacion

> [<- 03-datos](03-datos.md) | [README](README.md)

Como deployar el backend (stacks de recurso + stacks de Lambda), los
comandos devtools, rotar secrets y troubleshooting. Todo se opera con
`python devtools/run.py serverless <command>`.

## 1. Pre-requisitos

| Herramienta | Version min | Verificar |
|-------------|-------------|-----------|
| AWS CLI | 2.15+ | `aws --version` |
| AWS SAM CLI | 1.160+ | `sam --version` (`uv tool install aws-sam-cli`) |
| Python | 3.13+ | `python3 --version` |
| uv | 0.5+ | `uv --version` |
| psql | 16+ (opcional, para sesiones interactivas contra Neon) | `psql --version` |
| neonctl | reciente (opcional, gestionar branches Neon) | `neon --version` |
| jq, curl | recientes | — |

Setup inicial del modulo:

```bash
python devtools/run.py serverless init    # uv sync + verifica sam + aws CLI
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
> `deploy`, `deploy-infra`, `deploy-resource`, `destroy-resource` y `run`
> (contra un stage deployado) ejecutan `aws`/`sam` por debajo. Por
> defecto usan el perfil del shell (`AWS_PROFILE` o
> `[default]`), que puede apuntar a OTRA cuenta (ej. un perfil de otro
> proyecto) o tener el token SSO expirado. Por eso estos comandos aceptan
> `--aws-profile=tfs-dev`: inyecta `--profile tfs-dev` en los comandos
> `aws`/`sam` y garantiza que se opera sobre la cuenta del portfolio.
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

## 3. Deploy de los stacks

Los stacks de recurso van PRIMERO; los 4 Lambdas leen sus identificadores
desde SSM.

```bash
# 1. Todos los stacks de recurso (5 tablas DynamoDB + API GW + DLQ SQS)
python devtools/run.py serverless deploy-infra --stage=dev --aws-profile=tfs-dev

# 2. Los 4 stacks de Lambda (en cualquier orden entre si)
python devtools/run.py serverless deploy --lambda=db --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=contact_form --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=tracking_pixel --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=stream_processor --stage=dev --aws-profile=tfs-dev

# 3. Aplicar el schema PostgreSQL (invocando la Lambda db)
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/migrate.json --aws-profile=tfs-dev
```

`deploy-infra` deploya en orden los 7 stacks de recurso de
`serverless/lambda/resources/`. Para deployar (o redeployar) UN solo
recurso:

```bash
python devtools/run.py serverless deploy-resource \
  --name=dynamodb/contacts --stage=dev --aws-profile=tfs-dev
```

Para `stage` y `prod`: mismos comandos cambiando `--stage`. `deploy` arma
el artefacto `build/` del Lambda con uv (`uv pip install --target
build/`) + vendoring selectivo de `shared/`, y luego `sam deploy` solo
sube ese artefacto — NO corre `sam build` ni `pip`. `--guided` en el
primer deploy de cada uno.

`deploy` y `run` regeneran el `build/` del Lambda (deps con uv +
vendoring selectivo de los subpaquetes de `serverless/lambda/shared/` que
el Lambda usa, en `build/core/shared/`) antes de ejecutar; `build/` es
efimero y se limpia al terminar.

### Delete

No hay `Export`/`Fn::ImportValue` entre stacks, asi que el orden de
borrado es flexible. Aun asi conviene borrar los 4 stacks de Lambda
antes que los de recurso (para no dejar Event Source Mappings apuntando a
tablas inexistentes). Borrar UN recurso:

```bash
python devtools/run.py serverless destroy-resource \
  --name=dynamodb/contacts --stage=dev --confirm --aws-profile=tfs-dev
```

## 4. Desarrollo local

```bash
# Generar el SAM efimero desde lambda.yaml
python devtools/run.py serverless sam-generate --lambda=db --stage=dev

# Ejecutar el Lambda en local (--stage=local -> sam local invoke, sin AWS)
python devtools/run.py serverless run \
  --stage=local --lambda=db --event=events/current.json

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
| `sam-generate` | `lambda.yaml` -> `template.yaml` SAM efimero |
| `run --stage=<env>` | `--stage=local` -> `sam local invoke`; `--stage=dev\|stage\|prod` -> `aws lambda invoke` contra el deployado |
| `deploy` | Arma `build/` con uv + vendoring selectivo de `shared/`, luego `sam deploy` del artefacto (su stack) |
| `tests --type=<unit\|integration\|coverage>` | `pytest` del Lambda; sin target corre la suite completa, con `--shared` corre la libreria comun |

`deploy` y `run` (contra un stage deployado) aceptan
`--aws-profile=<perfil>` para fijar el perfil AWS CLI de los comandos
`aws`/`sam`. Usar SIEMPRE `--aws-profile=tfs-dev` (ver seccion 2.1).

### Infra / recursos

| Comando | Que hace |
|---------|----------|
| `deploy-infra` | Deploya en orden TODOS los stacks de recurso de `resources/`. Acepta `--aws-profile=tfs-dev` |
| `deploy-resource --name=<tipo>/<nombre>` | Deploya UN stack de recurso (`portfolio-<tipo>-<nombre>-<stage>`) |
| `destroy-resource --name=<tipo>/<nombre> --confirm` | Borra un stack de recurso |
| `list-resources` | Lista los recursos declarados en `resources/` |

### Setup / mantenimiento / calidad

| Comando | Que hace |
|---------|----------|
| `init` | Setup inicial (uv sync + verifica sam + aws CLI) |
| `clean` | Borra caches + artefactos efimeros (`template.yaml`, `build/`, `.aws-sam/`) |
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

> No existe ya el modo SAM monolitico ni un stack de infra unico: cada
> recurso es su propio stack (`deploy-resource`) y cada Lambda es su
> propio stack (`deploy --lambda=<nombre>`).

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
| `Parameter ... not found` (`{{resolve:ssm:...}}`) al deployar un Lambda | El stack de recurso no esta deployado en ese stage (el SSM param no existe) | `deploy-infra --stage=<stage>` (o `deploy-resource` del recurso faltante) primero |
| El Lambda falla en runtime con `Parameter ... not found` | El path SSM del nombre de tabla no existe — recurso no deployado | Deployar el stack de recurso correspondiente |
| Stack en `ROLLBACK_COMPLETE` | Recurso no creado en un deploy previo | `aws cloudformation delete-stack` + re-deploy |
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
