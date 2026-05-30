# 03 — Devtools provisioning (uses.invokes, uses.buckets, quitar SQS)

[← 02 shared](02-shared-foundations.md) · [siguiente: 04 send_email →](04-send-email-lambda.md)

> Fase 2. Extiende el provisioner para `uses.invokes` (Lambda→Lambda) y
> `uses.buckets` (S3 read), agrega el recurso `s3-bucket` + la tabla
> `email-config`, y ELIMINA todo lo de SQS. devtools es Python 3.14
> (`devtools/.venv/bin/python`). TDD con los tests en
> `devtools/tests/unit/src/serverless/`.

## 3.1 `uses.invokes` — invocación Lambda→Lambda (NUEVO)

En `devtools/serverless/provisioner.py`, `_build_statements`:

- Leer `uses.invokes: [<lambda-short-name>, ...]` (lista de nombres cortos;
  hoy el único target es `send_email`, invocado por contact_form/auth/users).
- Por cada target: agregar Statement IAM
  `{Effect:Allow, Action:['lambda:InvokeFunction'], Resource:
  'arn:aws:lambda:${region}:${account}:function:portfolio-<target>-${stage}'}`.
  (Usar el ARN base; el único target hoy es `send_email`, un Lambda `direct`
  sin SnapStart, invocado async por nombre `portfolio-send-email-${stage}`
  que resuelve a `$LATEST`.)
- Inyectar env var `LAMBDA_<TARGET_UPPER>_FUNCTION_NAME =
  portfolio-<target>-${stage>` en `_build_env_vars` (para que
  `shared.aws.lambda_invoke` resuelva el nombre sin hardcodear).
- El caller resuelve el nombre con
  `os.environ['LAMBDA_SEND_EMAIL_FUNCTION_NAME']`.

### Validación
- En el validador del manifest: `uses.invokes` debe ser lista de strings que
  resuelven a Lambdas existentes (`available_lambdas()`); error si no.

## 3.2 `uses.buckets` — S3 read (NUEVO)

En `_build_statements`:
- Leer `uses.buckets: [{name: portfolio-email-templates-${stage},
  access: read}]`.
- `read` → `['s3:GetObject']` sobre `arn:aws:s3:::<name>/*`; agregar también
  `s3:ListBucket` sobre `arn:aws:s3:::<name>` si se necesita (no por ahora).
- Inyectar env var `S3_<NAME_UPPER>_BUCKET = <name interpolado>`.
- `_SES`/`_DYNAMO` ya son el patrón a imitar (`_s3_statements` análogo a
  `_dynamodb_statements`).

## 3.3 Recurso `s3-bucket` (NUEVO) + tabla `email-config`

En `devtools/serverless/infra_provision.py`:
- Agregar `s3` a `_RESOURCE_TYPES` y `s3-bucket` a los kinds válidos.
- `_provision_s3_bucket(rendered)`: `aws s3api create-bucket` idempotente
  (`get-bucket-location` para detectar existencia), aplicar
  `put-public-access-block` (bloquear todo acceso público), `put-bucket-
  encryption` (SSE-S3), y publicar a SSM el `name`/`arn`.
- Crear `serverless/lambda/resources/s3/email-templates.yaml`:
  ```yaml
  kind: s3-bucket
  name: portfolio-email-templates-${stage}
  block_public_access: true
  encryption: true
  publishes_ssm:
    name: /portfolio/${stage}/s3/email-templates/name
    arn: /portfolio/${stage}/s3/email-templates/arn
  tags: { Project: portfolio, ManagedBy: devtools }
  ```
- Crear `serverless/lambda/resources/dynamodb/email-config.yaml`:
  ```yaml
  kind: dynamodb-table
  name: portfolio-email-config-${stage}
  billing_mode: PAY_PER_REQUEST
  hash_key: { name: kind, type: S }
  range_key: null
  stream: null
  point_in_time_recovery: false
  encryption: true
  ttl_attribute: null
  publishes_ssm:
    name: /portfolio/${stage}/dynamodb/email-config/name
    arn: /portfolio/${stage}/dynamodb/email-config/arn
  tags: { Project: portfolio, ManagedBy: devtools }
  ```
- `discover_resources()` debe recorrer también `s3/`.

## 3.4 Eliminar SQS de devtools

### Modificar `devtools/serverless/provisioner.py`
- `_build_trigger`: quitar la rama `ttype == 'sqs'`. Trigger válidos:
  `direct`, `http`.
- `TriggerSpec`: quitar `queue_name`, `batch_size`, `function_response_types`.
- `_build_statements`: quitar el bloque `uses.queues` (IAM SQS + SSM queue
  url paths) y `_SQS_ACTIONS`.
- `_wire_trigger` / `_rewire_trigger_on_update`: quitar la rama sqs.
- Borrar `_wire_sqs_trigger` completo.

### Modificar `devtools/serverless/infra_provision.py`
- Quitar `sqs` de `_RESOURCE_TYPES`, `sqs-queue` de los kinds, y
  `_provision_sqs_queue` completo + su rama en el dispatcher.
- Quitar `sqs/` de `discover_resources`.

### Modificar
- `devtools/serverless/lambda_controller.py`, `change_detector.py`,
  `flags.py`, `main.py`, `help.py`: quitar refs a sqs/queues/worker/
  stream_processor (el detalle exacto lo da la fase 6, archivo 07).
- Tests en `devtools/tests/unit/src/serverless/*`: actualizar/eliminar los
  que cubren trigger sqs, uses.queues, _provision_sqs_queue,
  stream_processor.

## 3.5 Seed de `email-config` + templates S3

Modelar análogo a `rate_limit_cmds.py` (que seedea `rate-limit-rules`):
- Agregar un comando devtools (o un command del Lambda `db`/un script) que:
  1. Sube los 20 templates (`serverless/lambda/services/send_email/seeds/templates/<kind>.{html,txt}`)
     al bucket `portfolio-email-templates-${stage}` (`aws s3 cp`).
  2. Hace `PutItem` de las 10 filas de `email-config` (PK=kind, bucket,
     html_path, txt_path, subject).
- Fuente de verdad de las 10 filas: un YAML/py en
  `serverless/lambda/services/send_email/seeds/email_config.py`.
- Decisión de ubicación del comando: nuevo subcomando
  `serverless seed-email-config --stage=<X>` en devtools (simétrico con
  `serverless setup-ssm` / `rate_limit_cmds`). Detalle en archivo 04.

## 3.6 Reglas

- **SIEMPRE** verificar devtools con `devtools/.venv/bin/python` (3.14), NO
  `python3` del shell. Ver skill `python-devtools`.
- **SIEMPRE** los recursos se declaran en `resources/<tipo>/*.yaml` (esquema
  plano devtools, sin IaC declarativa).
- **NUNCA** dejar código muerto de SQS "dormido".

## Archivos afectados (fase 2)

### Crear
- `serverless/lambda/resources/s3/email-templates.yaml`
- `serverless/lambda/resources/dynamodb/email-config.yaml`
- (tests devtools de `uses.invokes`, `uses.buckets`, `s3-bucket`)
  - Verificar: `test_runner --module=devtools --type=unit`

### Modificar
- `devtools/serverless/provisioner.py` — +invokes/+buckets, −sqs.
  - Verificar: `test_runner --module=devtools --type=unit`
- `devtools/serverless/infra_provision.py` — +s3, −sqs.
- `devtools/serverless/{lambda_controller,change_detector,flags,main,help}.py`
  — limpiar sqs/queues.
- `devtools/tests/unit/src/serverless/*` — actualizar/eliminar.

### Eliminar (fase 5, listado aquí por contexto)
- `serverless/lambda/resources/sqs/` completo (7 archivos).

[← 02 shared](02-shared-foundations.md) · [siguiente: 04 send_email →](04-send-email-lambda.md)
