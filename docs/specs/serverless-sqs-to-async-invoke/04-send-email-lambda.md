# 04 — Lambda `send_email` (puro: DynamoDB + S3 + Jinja2 + SES)

[← 03 devtools](03-devtools-provisioning.md) · [siguiente: 05 encoders →](05-encoders-refactor.md)

> Fase 3. Lambda `direct` puro de envío de email. NO toca Neon. Lee la
> config del email de DynamoDB (`email-config`), baja el template de S3,
> renderiza con Jinja2 y envía por SES. Sigue lambda-controller.

## 4.1 Estructura (scaffold lambda-controller)

```
serverless/lambda/services/send_email/
├── manifest.yaml
├── pyproject.toml            # deps: NINGUNA externa directa (todo via shared)
├── .gitignore
├── seeds/
│   ├── email_config.py       # las 10 filas {kind,bucket,html_path,txt_path,subject}
│   └── templates/
│       ├── register-magic-link.html / .txt
│       ├── login-magic-link.html / .txt
│       ├── password-reset.html / .txt
│       ├── email-change-verify.html / .txt
│       ├── register-code.html / .txt
│       ├── login-code.html / .txt
│       ├── email-changed.html / .txt
│       ├── account-disabled.html / .txt
│       ├── account-deleted.html / .txt
│       └── contact.html / .txt
├── core/
│   ├── handler.py            # direct: {operation:'email', action:'send', data}
│   ├── controllers/email/send.py     # clase Send(BaseController)
│   ├── services/email_service.py     # config + template + render + SES
│   ├── models/email.py               # EmailSendRequest (Pydantic)
│   └── settings/{config.py, operations.py}
└── tests/{unit,integration}/...
```

## 4.2 Contrato de invocación

`send_email` se invoca async con:

```json
{ "operation": "email", "action": "send",
  "data": {
    "kind": "register-code",
    "to": ["user@example.com"],
    "data": { "code": "ABC123", "expires_in_min": 15 },
    "reply_to": ["visitor@example.com"]
  } }
```

- `kind` (str, requerido) — clave en `email-config`.
- `to` (list[str], requerido) — destinatarios. Para `kind=contact` los pasa
  `contact_form` (owner emails); para auth/users el email del user.
- `data` (dict) — variables del template (Jinja2 context).
- `reply_to` (list[str], opcional) — sólo `contact` lo usa (email del
  visitante).

## 4.3 `email_service.py` (lógica)

```
1. config = get_email_config(kind)            # GET DynamoDB email-config[kind]
   - tabla resuelta de env var SSM_EMAIL_CONFIG_TABLE_PATH (uses.tables)
   - si no existe el kind -> EmailConfigNotFound -> code 1xxx (AC-6)
2. html_tpl = s3.get_object_text(config.bucket, config.html_path)
   txt_tpl  = s3.get_object_text(config.bucket, config.txt_path)
   - bucket también disponible en env var S3_EMAIL_TEMPLATES_BUCKET
     (uses.buckets); el de config debe coincidir.
3. subject = render_text(config.subject, data)
   html    = render_html(html_tpl, data)
   text    = render_text(txt_tpl, data)
4. from_address = get_secret_by_name('ses-from-address', local_env='EMAIL_FROM')
5. send_email(from_address=f'The Full Stack <{from}>', to_addresses=to,
              subject=subject, text_body=text, html_body=html,
              reply_to=reply_to)
```

Imports (todo via shared):
- `from shared.aws.dynamodb import get_table` (config)
- `from shared.aws.s3 import get_object_text`
- `from shared.templating.jinja import render_html, render_text`
- `from shared.aws.ses import send_email`
- `from shared.aws.ssm import get_secret_by_name`

## 4.4 `manifest.yaml`

```yaml
name: send-email
description: Lambda puro de envio de email (DynamoDB config + S3 template + SES).
runtime: python3.13
handler: core.handler.lambda_handler
memory: 256      # MB — MEDIR. SES + jinja2 + boto3 (dynamodb+s3+ses). Sin
                 # Neon (no sqlalchemy). Estimado 256; bajar a 128 sólo si la
                 # medicion lo permite (jinja2 pesa). Ver lambda-config.md.
timeout: 30
trigger:
  type: direct
uses:
  tables:
    email-config: read
  buckets:
    - name: portfolio-email-templates-${stage}
      access: read
  secrets:
    - ses-from-address
  sends-email: true
env:
  default:
    LOG_LEVEL: INFO
    AWS_SES_REGION: us-east-1
  prod:
    LOG_LEVEL: WARNING
```

> `memory`/`timeout` son provisionales: MEDIR con el procedimiento de
> `.claude/rules/lambda-config.md` y dejar el mínimo justificado.

## 4.5 Templates (migración del contenido existente)

- Los 9 kinds de auth/users → portar el contenido de
  `auth_email_worker/core/templates/es/<kind>.{html,txt}` a
  `send_email/seeds/templates/<kind>.{html,txt}`, **convirtiendo los
  placeholders** del render mustache-lite/`string.Template` (`${var}` o
  `{{var}}`) a sintaxis **Jinja2** (`{{ var }}`).
- `contact` → portar `contact_worker/core/templates/owner_email.{html,txt}`
  a `send_email/seeds/templates/contact.{html,txt}`, convirtiendo el
  mustache-lite (`{{#var}}block{{/var}}`) a Jinja2 (`{% if var %}...{% endif %}`).
- Los `subject` de cada kind: hoy viven en `template_service._SUBJECTS_ES`
  del worker (auth) y hardcoded en `persistence.py` (contact). Portar a la
  columna `subject` de cada fila de `email-config` (pueden ser Jinja2:
  `'Nuevo contacto de {{ name }}'`).

## 4.6 Seed (`serverless seed-email-config --stage=<X>`)

- Sube `seeds/templates/*` al bucket del stage (`aws s3 cp --recursive`).
- `PutItem` de las 10 filas desde `seeds/email_config.py`.
- Idempotente (overwrite). Detalle del comando devtools en archivo 03 §3.5.

## 4.7 Tests (TDD primero)

Unit (`tests/unit/`, un archivo por escenario, asserts exactos):
- `test_email_model_rejects_unknown_kind_missing.py` — kind requerido.
- `test_send_service_reads_config_from_dynamodb.py` — mock `get_table`.
- `test_send_service_unknown_kind_returns_error.py` — AC-6 (code 1xxx, sin SES).
- `test_send_service_renders_with_jinja.py` — mock S3 + assert render.
- `test_send_service_calls_ses_with_rendered_bodies.py` — mock `send_email`,
  assert subject/html/text/reply_to exactos.
- `test_send_controller_normalizes_success.py`.
- `test_handler_routes_email_send_to_controller.py`.
- `test_handler_rejects_unknown_operation.py`.

Integration (`tests/integration/`, opcional, con DynamoDB/S3/SES reales o moto).

## 4.8 Reglas
- **NUNCA** `import boto3`/`jinja2` en `core/` (sólo shared). lint-deps verde.
- **NUNCA** `send_email` toca Neon (es puro). Su cierre shared NO incluye
  `shared.db` (AC-16).
- **SIEMPRE** `to` lo provee el caller; `from_address` lo resuelve send_email.

## Archivos afectados (fase 3)

### Crear
- `serverless/lambda/services/send_email/**` (estructura completa arriba).
  - Verificar: `serverless tests --type=unit --lambda=send_email` (≥80%)
  - Verificar: `serverless lint-deps --lambda=send_email` exit 0

[← 03 devtools](03-devtools-provisioning.md) · [siguiente: 05 encoders →](05-encoders-refactor.md)
