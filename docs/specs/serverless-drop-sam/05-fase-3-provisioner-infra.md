# 05 — Fase 3: `infra_provision.py` (resources/ -> AWS CLI)

> [Anterior: 04](04-fase-2-provisioner-lambda.md) | [README](README.md) | [Siguiente: 06](06-fase-4-run-local.md)

Reemplazo de `infra_deploy.py`. Provisiona la infra compartida (tablas
DynamoDB, API Gateway REST, DLQ SQS) con AWS CLI directo, sin
CloudFormation. Depende de Fase 1 (`aws_cli.py` + `state.py`).

## Objetivo

Hoy [infra_deploy.py](../../../devtools/serverless/infra_deploy.py)
ensambla los fragmentos de `resources/` en un `infra.yaml` CloudFormation
y lo deploya con `aws cloudformation deploy`. Tras la migracion:

1. Los fragmentos de `resources/` dejan de ser CloudFormation: pasan al
   esquema plano de devtools (ver
   [02-arquitectura-objetivo.md](02-arquitectura-objetivo.md#5-esquema-de-los-yaml-de-infra-resources)).
2. `infra_provision.py` lee cada fragmento y emite las llamadas AWS CLI
   para crear el recurso, mas `aws ssm put-parameter` para publicar sus
   identificadores (que los Lambdas leen en runtime).

## Archivos afectados

### Crear

- `devtools/serverless/infra_provision.py` — render + provision de cada
  recurso de infra. Sustituye `infra_deploy.py`.
- `devtools/tests/unit/src/serverless/test_infra_render.py` — render del esquema.
- `devtools/tests/unit/src/serverless/test_infra_provision.py` — secuencia de
  llamadas AWS CLI (mockeado).

### Modificar

- `serverless/lambda/resources/_header.yaml` — ELIMINAR. El esquema
  devtools no necesita header CloudFormation.
- `serverless/lambda/resources/dynamodb/contacts.yaml` — reescribir al
  esquema devtools (`kind: dynamodb-table`, sin `Transform`/`Fn::Sub`).
- `serverless/lambda/resources/dynamodb/tracking.yaml` — idem.
- `serverless/lambda/resources/dynamodb/cache.yaml` — idem.
- `serverless/lambda/resources/dynamodb/rate-limit-rules.yaml` — idem.
- `serverless/lambda/resources/dynamodb/rate-limit-buckets.yaml` — idem.
- `serverless/lambda/resources/api_gateway/portfolio-api.yaml` —
  reescribir (`kind: rest-api`, con su rol CloudWatch y access log).
- `serverless/lambda/resources/sqs/stream-processor-dlq.yaml` —
  reescribir (`kind: sqs-queue`).

### Eliminar

- `devtools/serverless/infra_deploy.py` — sustituido por
  `infra_provision.py`.

## Esquemas de recurso del esquema devtools

`infra_provision.py` soporta tres `kind`:

### `kind: dynamodb-table`

```yaml
kind: dynamodb-table
name: portfolio-contacts-${stage}
billing_mode: PAY_PER_REQUEST
hash_key: { name: id, type: S }
range_key: null                   # opcional
stream: NEW_AND_OLD_IMAGES        # o null si la tabla no tiene stream
point_in_time_recovery: true
encryption: true
ttl_attribute: null               # ej. expires_at en la tabla tracking
publishes_ssm:
  name: /portfolio/${stage}/dynamodb/contacts/name
  arn: /portfolio/${stage}/dynamodb/contacts/arn
  stream_arn: /portfolio/${stage}/dynamodb/contacts/stream-arn
tags: { Project: portfolio, ManagedBy: devtools }
```

-> `aws dynamodb create-table` + `aws dynamodb update-time-to-live` (si
`ttl_attribute`) + `aws ssm put-parameter` (uno por entrada de
`publishes_ssm`).

### `kind: rest-api`

```yaml
kind: rest-api
name: portfolio-api-${stage}
endpoint_type: REGIONAL
access_log_group: /aws/apigateway/portfolio-api-${stage}
access_log_retention_days: 7
cloudwatch_role_name: portfolio-api-cwlogs-role-${stage}
publishes_ssm:
  id: /portfolio/${stage}/api_gateway/portfolio-api/id
  root_resource_id: /portfolio/${stage}/api_gateway/portfolio-api/root-resource-id
  access_log_group_arn: /portfolio/${stage}/api_gateway/portfolio-api/access-log-group-arn
```

-> `aws iam create-role` (rol CloudWatch) + `aws apigateway
update-account` + `aws logs create-log-group` + `aws apigateway
create-rest-api` + `aws ssm put-parameter`.

### `kind: sqs-queue`

```yaml
kind: sqs-queue
name: portfolio-stream-processor-dlq-${stage}
message_retention_seconds: 1209600   # 14 dias
publishes_ssm:
  arn: /portfolio/${stage}/sqs/stream-processor-dlq/arn
  url: /portfolio/${stage}/sqs/stream-processor-dlq/url
```

-> `aws sqs create-queue` + `aws ssm put-parameter`.

## API publica de `infra_provision.py`

```python
def discover_resources() -> list[Path]:
    """Lista los *.yaml de serverless/lambda/resources/ (sin _header)."""

def render_resource(path: Path, *, stage: str) -> RenderedResource:
    """Funcion pura: fragmento YAML -> RenderedResource con ${stage} interpolado."""

def provision_infra(
    *, stage: str, profile: str | None, region: str,
) -> InfraState:
    """Provisiona TODOS los recursos de resources/. Idempotente.

    Por cada recurso: si existe (describe-*), actualiza lo actualizable;
    si no, lo crea. Publica los SSM. Registra en .state/infra-<stage>.json.
    """

def deprovision_infra(
    *, stage: str, profile: str | None, region: str,
) -> None:
    """Borra todos los recursos de infra del stage en orden inverso."""
```

## Idempotencia sin CloudFormation

Cada recurso se reconcilia consultando AWS:

- DynamoDB: `aws dynamodb describe-table`. Si existe, NO se recrea
  (DynamoDB casi nada es mutable post-creacion salvo TTL y billing).
  Solo se re-publican los SSM.
- API Gateway: `aws apigateway get-rest-apis` filtrado por nombre. Si
  existe, se reutiliza el Id.
- SQS: `aws sqs get-queue-url`. Si existe, se reutiliza.

El `.state/infra-<stage>.json` guarda los identificadores para el
`deprovision`.

## Orden de provision / deprovision

```text
Provision (orden):
  1. SQS DLQ          (sin dependencias)
  2. DynamoDB tables  (sin dependencias entre si)
  3. API Gateway REST (sin dependencias; los metodos los agrega el
                       provisioner del Lambda)

Deprovision (orden inverso):
  3. API Gateway REST
  2. DynamoDB tables
  1. SQS DLQ
```

Las tablas no dependen entre si — el orden interno es irrelevante. La
API se crea vacia; sus metodos `/contact` y `/track` los agrega
`provisioner.py` (Fase 2) al deployar `contact_form` y `tracking_pixel`.

## Criterios de aceptacion

- **AC-3.1**: Given un fragmento `kind: dynamodb-table` con
  `${stage}`, When `render_resource(stage='dev')`, Then todos los
  `${stage}` quedan interpolados a `dev`.
- **AC-3.2**: Given un `kind: dynamodb-table` con `stream`, When
  `provision_infra`, Then se llama `create-table` con
  `--stream-specification` y se publica el `stream_arn` en SSM.
- **AC-3.3**: Given una tabla que ya existe, When `provision_infra`,
  Then NO se llama `create-table` (solo se re-publican los SSM).
- **AC-3.4**: Given un `kind: rest-api`, When `provision_infra`, Then se
  crea el rol CloudWatch, el log group, la REST API y se publican los 3
  SSM.
- **AC-3.5**: Given infra desplegada, When `deprovision_infra`, Then se
  borran API, tablas y DLQ en orden inverso y el
  `.state/infra-<stage>.json` se vacia.
- **AC-3.6**: Given `provision_infra` corrida dos veces seguidas, When
  termina la segunda, Then no hubo errores y el estado es consistente
  (idempotencia).
- **AC-3.7**: When se busca `Transform` o `Fn::` en
  `serverless/lambda/resources/`, Then no hay resultados (los fragmentos
  ya no son CloudFormation).

## Tests requeridos

`test_infra_render.py` — funcion pura, fixtures de los 3 `kind`:

- `test_render_interpolates_stage` [AC-3.1]
- `test_render_dynamodb_table_with_stream`
- `test_render_rest_api_fields`
- `test_render_sqs_queue_fields`

`test_infra_provision.py` — `aws_cli.aws` mockeado:

- `test_provision_dynamodb_with_stream_publishes_ssm` [AC-3.2]
- `test_provision_skips_create_when_table_exists` [AC-3.3]
- `test_provision_rest_api_creates_role_loggroup_api_ssm` [AC-3.4]
- `test_deprovision_reverse_order` [AC-3.5]
- `test_provision_is_idempotent` [AC-3.6]

## Verificacion incremental con comandos devtools

Esta fase agrega `provision-infra` al CLI (via el toque minimo de
`main.py`). Es el primer comando nuevo de la migracion que se puede
ejecutar:

```bash
# Sin AWS — el dry-run renderiza los recursos y muestra que haria
python devtools/run.py serverless provision-infra --stage=dev --dry-run
python devtools/run.py serverless tests --type=unit         # suite sigue verde
python devtools/run.py serverless help                      # provision-infra listado

# Con acceso a AWS dev (perfil tfs-dev) — aprovisiona la infra real:
python devtools/run.py serverless provision-infra --stage=dev --aws-profile=tfs-dev
# verificar que las tablas / API / DLQ existen y los SSM se publicaron:
aws dynamodb list-tables --region us-east-1 --profile tfs-dev \
  --query "TableNames[?starts_with(@,'portfolio-')]"
aws ssm get-parameters-by-path --path /portfolio/dev/dynamodb \
  --recursive --region us-east-1 --profile tfs-dev --query 'Parameters[*].Name'
# idempotencia: re-ejecutar no debe fallar
python devtools/run.py serverless provision-infra --stage=dev --aws-profile=tfs-dev
```

`provision-infra --dry-run` es OBLIGATORIO en esta fase (no necesita
AWS). El `provision-infra` real se ejecuta si hay acceso a la cuenta dev;
si no, se documenta como pendiente y se corre en la Fase 8. NO se cierra
la fase sin que al menos el `--dry-run` pase y renderice los 7 recursos.

## Verificacion (Definition of Done de la fase)

```bash
devtools/.venv/bin/python -m pytest devtools/tests/unit/src/serverless/test_infra_render.py devtools/tests/unit/src/serverless/test_infra_provision.py -v
python devtools/run.py docker lint --module=devtools
devtools/.venv/bin/python -m mypy devtools/serverless/infra_provision.py
rg "Transform|Fn::" serverless/lambda/resources/   # debe dar 0 resultados
# comandos devtools:
python devtools/run.py serverless provision-infra --stage=dev --dry-run
python devtools/run.py serverless tests --type=unit
```

- [ ] AC-3.1..AC-3.7 cubiertos
- [ ] `provision-infra --dry-run` renderiza los 7 recursos sin error
- [ ] `provision-infra` real verificado en dev (o documentado pendiente)
- [ ] Coverage >= 80% per-file en `infra_provision.py`
- [ ] Los 7 fragmentos de `resources/` reescritos al esquema devtools
- [ ] `_header.yaml` eliminado
- [ ] `infra_deploy.py` eliminado
- [ ] Ruff + mypy sin errores

---

[Anterior: 04](04-fase-2-provisioner-lambda.md) | [README](README.md) | [Siguiente: 06](06-fase-4-run-local.md)
