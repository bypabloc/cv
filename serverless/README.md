# serverless/

> Backend serverless del portfolio: 3 Lambdas Python 3.13 en us-east-1
> que reciben el form de contacto, tracking pixel y validan Turnstile.
> Stack IaC: AWS SAM. Costo estimado ~$7/mes (dominado por WAF Web ACL).

## Indice

| Documento | Cuando leer |
|-----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Antes de tocar cualquier archivo. Estructura completa de carpetas + diagramas ASCII (flujo `/contact`, `/track`, capas defense-in-depth, datos, deploy) |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Antes del primer `sam deploy`. Pasos exactos para setup AWS account + Turnstile + DNS |
| [RUNBOOK.md](RUNBOOK.md) | Operaciones post-deploy: rotar secrets, tail logs, alarmas, troubleshooting |
| [docs/api-contract.md](docs/api-contract.md) | Cuando modifiques request/response shape de un endpoint |
| [docs/data-model.md](docs/data-model.md) | Cuando modifiques schema de DynamoDB |
| [docs/secrets.md](docs/secrets.md) | Inventario de SSM Parameters y KMS keys |
| [docs/monitoring.md](docs/monitoring.md) | Dashboards, alarmas, queries Logs Insights |
| [docs/waf-rules.md](docs/waf-rules.md) | Detalle de cada regla WAF + ajustes de limit |
| [docs/ses-setup.md](docs/ses-setup.md) | DKIM/SPF/DMARC exactos para Cloudflare DNS |
| [docs/adr/](docs/adr/) | Decision log — leer antes de cuestionar una decision tomada |

## Reglas criticas

1. **NUNCA** modificar `template.yaml` sin correr `sam validate` despues
2. **NUNCA** commitear `.env.dev`, `.env.prod`, `samconfig.toml.local` ni
   archivos de output `.aws-sam/`
3. **SIEMPRE** Python 3.13 (managed runtime), arm64 Graviton2
4. **SIEMPRE** Powertools v3 (`@logger`, `@tracer`, `@metrics`) en cada handler
5. **SIEMPRE** secrets via SSM Parameter Store + KMS, NO en env vars planos
6. **SIEMPRE** IAM least privilege: acciones especificas + ARN especifico
7. **SIEMPRE** WAF rate-based rule per-IP (API Gateway throttle es global)
8. **SIEMPRE** tests `pytest -m unit` >= 80% coverage antes de `sam deploy`
9. **NUNCA** atribucion de IA en commits, codigo o docstrings

## Skills relacionadas

Para preguntas tecnicas, invocar las skills consolidadas:

- `/aws-lambda-python` — handlers, Powertools, cold start, IAM
- `/aws-api-gateway` — REST API, throttling, WAF rate-based, CORS
- `/aws-dynamodb` — tablas, On-Demand, TTL, boto3
- `/aws-ses` — email transaccional, DKIM/SPF/DMARC
- `/cloudflare-turnstile` — captcha widget, siteverify, idempotency

## Comandos rapidos

```bash
# Setup primera vez
cd serverless/
uv sync
cp env/.env.example env/.env.dev   # completar values

# Test local
pytest tests/unit -v --cov
sam local invoke ContactFormFunction --event events/contact_form_valid.json
sam local start-api --port 3000

# Deploy
sam build --use-container
sam deploy --guided    # 1ra vez
sam deploy             # subsiguientes

# Operaciones
sam logs -n ContactFormFunction --tail
./scripts/smoke_test.sh
./scripts/verify_ses_dns.sh
```

## Navegacion

- [.. (root del portfolio)](..)
- [.claude/docs/ (knowledge base de los 5 servicios)](../.claude/docs)
- [.claude/skills/ (skills invocables)](../.claude/skills)
