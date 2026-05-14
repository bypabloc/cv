# AWS Lambda knowledge base

> Conocimiento consolidado sobre como desplegar y mantener Lambdas Python 3.13
> para el portfolio (contact-form, turnstile-validator, tracking-pixel). Cada
> nodo cubre un tema; navegar por relevancia, no leer linealmente.

## Cuando leer cada archivo

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Modelo de ejecucion Lambda 2026 | [01-architecture.md](./01-architecture.md) | Entender runtime managed, event loop, cold start, SnapStart, x86 vs arm64 |
| Estructura del handler y tipos de event | [02-handler-patterns.md](./02-handler-patterns.md) | API Gateway REST vs HTTP, response shapes, return values |
| AWS Lambda Powertools v3 | [03-powertools.md](./03-powertools.md) | Logger, tracer, metrics, validator con Pydantic v2, decorators |
| Optimizacion de cold start | [04-cold-start-optimization.md](./04-cold-start-optimization.md) | Init phase, lazy loading, layers, SnapStart trade-offs, package size |
| Deployment con AWS SAM | [05-deployment-sam.md](./05-deployment-sam.md) | SAM template.yaml completo, build, deploy, sam local, sam logs |
| IAM least privilege | [06-iam-security.md](./06-iam-security.md) | Roles por Lambda, policies estrictas, Secrets Manager, KMS |
| Observability | [07-observability.md](./07-observability.md) | CloudWatch Logs, X-Ray tracing, structured logging, correlacion IDs |
| Costos y pricing 2026 | [08-cost-optimization-2026.md](./08-cost-optimization-2026.md) | Free tier, pricing, estimaciones para este proyecto |
| Comparacion vs alternativas | [09-lambda-vs-alternatives.md](./09-lambda-vs-alternatives.md) | Lambda vs Workers vs Vercel vs App Runner |

## Reglas criticas

- NUNCA hardcodear secretos (Turnstile key, SES credentials) — usar
  Secrets Manager o SSM Parameter Store, encryptado con KMS.
- NUNCA usar IAM managed policies amplias (`AmazonDynamoDBFullAccess`,
  `AmazonSESFullAccess`) — crear policies inline con permisos minimos.
- SIEMPRE especificar memory correcta en SAM (256-1024MB tipico para
  contact-form). Memory determina CPU allocation y pricing.
- SIEMPRE activar X-Ray tracing (`TracingConfig: Active` en SAM) para
  debugging en produccion.
- SIEMPRE usar Python 3.13 runtime (soporte hasta Oct 2029). No usar 3.9
  (termina Dec 2025) ni 3.11.
- NUNCA commitear `samconfig.toml` si contiene stacks names privados o
  S3 buckets. Generalizarlo o excluir del repo.

## Quick start: desplegar una Lambda

```bash
# 1. Instalar SAM CLI
curl https://aws-serverless-tools-telemetry.us-east-1.amazonaws.com/linux/x86_64/latest/aws-sam-cli-linux-x86_64.zip -o sam-cli.zip
unzip sam-cli.zip -d sam-installation
./sam-installation/install --update

# 2. Crear y validar template
sam init --runtime python3.13 --name contact-form
sam validate --template template.yaml

# 3. Build
sam build --use-container

# 4. Deploy (guidado)
sam deploy --guided

# 5. Invocar local
sam local invoke ContactFormFunction -e events/contact.json

# 6. Ver logs
sam logs -n ContactFormFunction --stack-name my-stack --tail
```

## Estado actual (Mayo 2026)

- 3 Lambdas planeadas: contact-form, turnstile-validator, tracking-pixel
- Region: us-east-1 (Oregon)
- Runtime: Python 3.13.x (managed)
- IaC: AWS SAM (template.yaml)
- Deployment: local via `sam deploy` (no CI todavia)
- Observability: CloudWatch Logs + X-Ray (opt-in SnapStart para cold start)
- Pricing estimado: <$5 USD/mes (ambos dentro free tier)

Verificado a fecha 2026-05-13.
