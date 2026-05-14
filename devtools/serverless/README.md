# Serverless CLI

> Gestion del backend SAM del portfolio (Lambdas Python 3.13 arm64 + API
> Gateway + DynamoDB + SES + Neon PostgreSQL en us-west-2).

## Uso

```bash
python devtools/run.py serverless <command> [--stage=local] [flags...]
```

## Stages

| Stage | Descripcion |
| ----- | ----------- |
| `local` | sam local invoke / start-api con moto mocks (sin AWS) |
| `dev` | Stack desplegado en us-west-2 (sandbox / dev account) |
| `prod` | Stack desplegado en us-west-2 (productiva) |

> `local` no es un stage AWS real. Para ese path, los commands llaman
> `sam local invoke` y `sam local start-api` apuntando a `events/` y
> `moto` mocks definidos en `serverless/tests/conftest.py`.

## Functions

| Function | Path Lambda | Trigger |
| -------- | ----------- | ------- |
| `contact-form` | `src/contact_form/` | API GW POST /contact |
| `tracking-pixel` | `src/tracking_pixel/` | API GW POST /track |
| `turnstile-validator` | `src/turnstile_validator/` | API GW POST /validate-turnstile (interno) |
| `stream-processor` | `src/stream_processor/` | DynamoDB Streams (contacts + tracking) -> Neon PG |
| `aggregator` | `src/aggregator/` | EventBridge cron diario -> agregaciones a Neon PG |

## Comandos

### Lifecycle

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| `init` | Setup inicial (uv sync + verifica sam + aws CLI) | |
| `validate` | `sam validate template.yaml` | |
| `build` | `sam build --use-container` | `--no-cache`, `--function=NAME` |
| `deploy` | `sam deploy --config-env <stage>` | `--stage`, `--guided`, `--parameter-overrides` |
| `delete` | `sam delete` del stack | `--stage`, `--confirm`, `--dry-run` |

### Local development

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| `invoke` | `sam local invoke <Function> --event <X>` | `--function`, `--event`, `--debug` |
| `start-api` | `sam local start-api` (server HTTP) | `--port=3000`, `--debug` |
| `logs` | `sam logs -n <function>` | `--function`, `--tail`, `--since=10m`, `--filter` |
| `tail` | Alias de `logs --tail` | `--function`, `--since` |

### Quality

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| `lint` | Ruff check sobre `src/` + `tests/` | `--module-path`, `--files`, `--output-format` |
| `lint-fix` | Ruff check --fix | `--module-path`, `--files` |
| `format` | Ruff format | `--module-path`, `--files` |
| `typecheck` | mypy --strict sobre `src/` | `--module-path` |

### Tests

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| `test` | pytest unit + integration con coverage | `--verbose`, `--coverage-threshold=80` |
| `test-unit` | pytest tests/unit -m unit | `--verbose`, `--marker`, `--files` |
| `test-integration` | pytest tests/integration -m integration | `--verbose`, `--marker` |
| `test-coverage` | pytest --cov + HTML report | `--coverage-threshold=80` |

### Secrets / Setup AWS resources fuera del template

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| `setup-ssm` | Crear SSM Parameter (KMS) | `--name`, `--value` (stdin si falta), `--key-id` |
| `rotate-secret` | Rotar valor de un SSM Parameter | `--name`, `--value`, `--confirm` |
| `verify-ses-dns` | `dig` DKIM/SPF/DMARC vs Cloudflare | |
| `request-ses-prod` | Plantilla del ticket de production access SES | |

### Database (Neon PostgreSQL)

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| `db-shell` | psql interactivo contra Neon | `--stage`, `--branch` |
| `db-migrate` | Aplicar migrations pendientes | `--stage`, `--sql-file`, `--dry-run` |
| `db-rollback` | Rollback ultima migration (DESTRUCTIVO) | `--stage`, `--confirm`, `--dry-run` |
| `db-seed` | Cargar data de prueba | `--stage`, `--dry-run` |
| `db-branch <action>` | CRUD branches Neon (create/list/delete) | `--branch`, `--parent`, `--confirm` |
| `db-tables` | Listar tablas + row counts | `--stage`, `--output=json` |

### Observability

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| `metrics` | Resumen CloudWatch (Lambda + API GW + WAF) | `--stage`, `--since`, `--output` |
| `alarms` | Lista alarmas + estado | `--stage`, `--output` |

### Maintenance

| Comando | Descripcion | Flags |
| ------- | ----------- | ----- |
| `smoke` | Smoke test (curl endpoint deployed) | `--stage` |
| `clean` | `rm -rf .aws-sam/ + caches Python` | `--dry-run` |
| `help` | Ayuda colorizada | |

## Ejemplos

```bash
# Setup primera vez
python devtools/run.py serverless init
python devtools/run.py serverless setup-ssm --name=/portfolio/turnstile-secret
python devtools/run.py serverless setup-ssm --name=/portfolio/neon-url

# Desarrollo local
python devtools/run.py serverless validate
python devtools/run.py serverless build
python devtools/run.py serverless invoke --function=contact-form \
    --event=events/contact_form_valid.json
python devtools/run.py serverless start-api --port=3000

# Calidad pre-commit
python devtools/run.py serverless lint
python devtools/run.py serverless format
python devtools/run.py serverless typecheck
python devtools/run.py serverless test --coverage-threshold=80

# Deploy a dev
python devtools/run.py serverless deploy --stage=dev --guided  # primera vez
python devtools/run.py serverless deploy --stage=dev           # subsiguientes
python devtools/run.py serverless smoke --stage=dev

# Logs / debugging
python devtools/run.py serverless logs --function=contact-form --tail
python devtools/run.py serverless metrics --stage=dev
python devtools/run.py serverless alarms --stage=prod

# Database (Neon)
python devtools/run.py serverless db-shell --stage=dev
python devtools/run.py serverless db-migrate --stage=dev --dry-run
python devtools/run.py serverless db-migrate --stage=dev
python devtools/run.py serverless db-branch create --branch=feature-X
python devtools/run.py serverless db-tables --stage=prod --output=json

# Limpieza
python devtools/run.py serverless clean --dry-run
python devtools/run.py serverless clean
```

## Patron arquitectonico

Sigue exactamente el patron de `devtools/docker/`:

1. **Comando posicional + flags**: `serverless build --no-cache` (NO
   `--command=build`). Politica documentada en
   [`.claude/rules/devtools.md`](../../.claude/rules/devtools.md).
2. **Modulos por dominio**:
   - `lifecycle.py` — build, deploy, invoke, start-api, logs, clean
   - `quality.py` — lint, format, typecheck
   - `testing.py` — pytest unit + integration + coverage
   - `secrets.py` — SSM Parameters, SES DNS verify
   - `database.py` — Neon PG (shell, migrate, branch, tables)
   - `observability.py` — CloudWatch metrics + alarms
   - `help.py` — ayuda colorizada
3. **Validacion centralizada**: `flags.py` con `VALID_COMMANDS`,
   `ALLOWED_FLAGS`, `DESTRUCTIVE_COMMANDS`, `JSON_OUTPUT_COMMANDS`.
4. **Exit codes consistentes**: 0 OK, 1 error de ejecucion, 2 error
   de validacion de flags, 130 Ctrl+C.
5. **Destructivo requiere `--confirm` o `--dry-run`**: enforced en
   `flags.validate()` antes de invocar handler.

## Conocimiento relacionado

- `.claude/docs/aws-lambda/` + skill `aws-lambda-python`
- `.claude/docs/aws-api-gateway/` + skill `aws-api-gateway`
- `.claude/docs/aws-dynamodb/` + skill `aws-dynamodb`
- `.claude/docs/aws-ses/` + skill `aws-ses`
- `.claude/docs/cloudflare-turnstile/` + skill `cloudflare-turnstile`
- `.claude/docs/postgresql-18-analytics/` (no skill, complementa `postgresql-18`)
- `.claude/docs/neon/` + skill `neon`
- `serverless/ARCHITECTURE.md` — estructura completa + diagramas de flujo
