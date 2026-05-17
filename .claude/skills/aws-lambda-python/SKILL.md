---
name: aws-lambda-python
description: >
  AWS Lambda reference for Python 3.13 runtime in this portfolio (us-west-2,
  contact-form + tracking-pixel + stream-processor handlers). Covers
  managed runtime support (Python 3.13 official since Nov 2024, LTS to Oct
  2029), SnapStart for Python (Nov 2025, ~10x cold start reduction),
  Graviton2 arm64 (-20% cost +19% perf vs x86_64), AWS Lambda Powertools
  v3 (logger / tracer / metrics / validator / idempotency), cold start
  optimization (lazy imports, layers, package size, boto3 client caching),
  IAM least privilege patterns, KMS-encrypted SSM Parameter Store for
  secrets (NOT plain env vars), CloudWatch Logs retention, X-Ray tracing,
  pricing 2026 us-west-2 (free tier 1M invocations + 400k GB-sec
  perpetual), and Lambda vs Workers/Vercel/App Runner/Fargate comparison.
  ALWAYS invoke this skill BEFORE answering ANY question about AWS Lambda
  Python in this project, including questions framed only as "lambda
  handler" or "serverless function" without explicitly saying AWS. NEVER
  answer Lambda questions from training data alone — this project has
  consolidated 2026 knowledge (runtime versions, Powertools v3 API,
  SnapStart for Python release date, arm64 pricing, free tier perpetual)
  that override generic advice.
  Use when the user says "lambda", "aws lambda", "lambda python",
  "python 3.13 lambda", "lambda handler", "handler aws", "powertools",
  "aws powertools", "@logger", "@tracer", "@metrics", "snapstart",
  "lambda snapstart", "cold start", "init phase", "graviton2 lambda",
  "arm64 lambda", "lambda layer", "lambda layers", "container image
  lambda", "lambda zip", "boto3 client cache", "lambda iam role",
  "lambda least privilege", "ssm parameter lambda", "secrets manager
  lambda", "kms lambda", "cloudwatch logs lambda", "x-ray lambda",
  "lambda pricing", "lambda free tier", "lambda cost", "costo lambda",
  "lambda vs workers", "lambda vs cloudflare workers", "lambda vs
  vercel", "lambda vs fargate", "como creo una lambda", "como hago una
  lambda", "lambda en python", "lambda con python", "serverless aws",
  "function aws", "lambda timeout", "lambda memory", "lambda 10gb",
  "lambda 15 min", "lambda concurrency", "provisioned concurrency",
  "lambda reserved concurrency", "lambda throttle", "lambda 429".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash(sam:*), Bash(aws:*)
argument-hint: "tema: runtime | handler | powertools | cold-start | deploy | iam | observability | cost | alternativas"
metadata:
  version: "1.0"
---

# AWS Lambda Python 3.13 — knowledge reference

> Conocimiento consolidado sobre AWS Lambda con Python 3.13 para el
> backend del portfolio (3 funciones en us-west-2: contact-form,
> tracking-pixel, stream-processor). Toda decision, gotcha y
> procedimiento esta en `.claude/docs/aws-lambda/`.

## Pre-requisito OBLIGATORIO

Antes de responder cualquier pregunta sobre AWS Lambda, leer la doc
relevante de `.claude/docs/aws-lambda/`:

| Tema de la pregunta | Archivo a leer |
|---------------------|----------------|
| Runtime, cold start anatomy, SnapStart, arm64 | [01-architecture.md](../../docs/aws-lambda/01-architecture.md) |
| Handler patterns (event/context, response shape) | [02-handler-patterns.md](../../docs/aws-lambda/02-handler-patterns.md) |
| Powertools v3 (logger/tracer/metrics/validator) | [03-powertools.md](../../docs/aws-lambda/03-powertools.md) |
| Cold start optimization (lazy load, layers, size) | [04-cold-start-optimization.md](../../docs/aws-lambda/04-cold-start-optimization.md) |
| AWS SAM deployment, template.yaml, sam local | [05-deployment-sam.md](../../docs/aws-lambda/05-deployment-sam.md) |
| IAM least privilege, KMS, SSM Parameter Store | [06-iam-security.md](../../docs/aws-lambda/06-iam-security.md) |
| CloudWatch Logs, X-Ray, metrics, alarms | [07-observability.md](../../docs/aws-lambda/07-observability.md) |
| Pricing 2026 us-west-2, free tier, tuning | [08-cost-optimization-2026.md](../../docs/aws-lambda/08-cost-optimization-2026.md) |
| Lambda vs Workers/Vercel/App Runner/Fargate | [09-lambda-vs-alternatives.md](../../docs/aws-lambda/09-lambda-vs-alternatives.md) |

Si la pregunta toca multiples temas, leer todos los relevantes y
sintetizar.

## Reglas criticas (siempre activas)

1. **SIEMPRE** Python 3.13 (managed runtime oficial desde Nov 2024). NO
   intentar Python 3.14 en Lambda — solo disponible via container
   image custom, adds complexity sin beneficio para este caso.

2. **SIEMPRE** arm64 (Graviton2): -20% costo vs x86_64, +19% performance,
   100% compatibilidad con boto3/Powertools/httpx. Solo usar x86_64 si
   hay binary depend que no compile en arm.

3. **SIEMPRE** AWS Lambda Powertools v3 desde el inicio: `@logger`,
   `@tracer`, `@metrics` como decorators del handler. Sin Powertools
   = plumbing manual de JSON logs y correlation IDs.

4. **NUNCA** secrets en env vars planos. Usar SSM Parameter Store
   `SecureString` + KMS encryption. Lambda lee con `ssm:GetParameter` +
   `kms:Decrypt`. Para Turnstile secret, DB passwords, API keys.

5. **NUNCA** instalar boto3 manualmente — ya viene en runtime managed.
   Solo agregar lo extra (Powertools, httpx, jsonschema). Reduce
   package size = cold start mas rapido.

6. **SIEMPRE** boto3 client en module scope (no dentro del handler).
   ```python
   import boto3
   dynamodb = boto3.resource('dynamodb')  # init phase, reusado entre invokes

   def handler(event, context):
       dynamodb.Table('contacts').put_item(Item=...)
   ```
   Patron incorrecto: instanciar boto3 dentro de handler = nueva
   connection cada invocacion = +200ms latencia.

7. **NUNCA** Lambda con managed policies amplias (ej. `AmazonDynamoDBFullAccess`).
   Custom inline policy con resource ARN especifico + action especifica.
   Ej: `dynamodb:PutItem` en `arn:aws:dynamodb:us-west-2:*:table/contacts`.

8. **SIEMPRE** verificar la skill antes de modificarla con
   `claude --permission-mode bypassPermissions -p` (regla
   [.claude/rules/claude-config-testing.md](../../rules/claude-config-testing.md)).

## Workflow tipico de respuesta

1. Identificar el tema del prompt (runtime / handler / deploy / cost / etc.)
2. Leer el(los) archivo(s) relevante(s) de `.claude/docs/aws-lambda/`
3. Responder con:
   - Causa raiz (si es un error)
   - Codigo Python ejecutable (no pseudocode)
   - Snippet SAM YAML si toca infra
   - Verificacion: como confirmar que funciona (`sam local invoke`, logs)
4. Si la pregunta cae fuera de scope: derivar a otra skill o decir que
   no esta cubierto

## Atajos rapidos para preguntas frecuentes

### "Como hago una Lambda Python para el form de contacto?"

Leer [02-handler-patterns.md](../../docs/aws-lambda/02-handler-patterns.md)
y [03-powertools.md](../../docs/aws-lambda/03-powertools.md). Estructura
minima:

```python
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger(service='contact-form')
tracer = Tracer()
metrics = Metrics(namespace='portfolio')

@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics
def handler(event: dict, context: LambdaContext) -> dict:
    body = json.loads(event['body'])
    # validate, dynamodb.put_item, ses.send_email
    return {'statusCode': 200, 'body': json.dumps({'ok': True})}
```

### "Cuanto va a costar?"

Para este portfolio (~5,100 invocations/mes): **$0/mes** (free tier
perpetuo de 1M req + 400k GB-sec). Detalle en
[08-cost-optimization-2026.md](../../docs/aws-lambda/08-cost-optimization-2026.md).

### "Vale la pena SnapStart para Python?"

Hoy NO — overhead de configuracion + posible cold restore latency. Solo
considerar post-launch si el cold start de 300-400ms es problematico
para el form de contacto. Detalle en
[04-cold-start-optimization.md](../../docs/aws-lambda/04-cold-start-optimization.md).

### "Como manejo el secret de Turnstile?"

NUNCA env var planos. SSM Parameter Store `SecureString` + KMS:

```bash
aws ssm put-parameter \
  --name /portfolio/turnstile-secret \
  --type SecureString \
  --value "ACTUAL_SECRET_FROM_CLOUDFLARE" \
  --key-id alias/portfolio-lambdas \
  --region us-west-2
```

Lambda lee con Powertools `parameters.get_parameter('/portfolio/turnstile-secret', decrypt=True)`.
Detalle en [06-iam-security.md](../../docs/aws-lambda/06-iam-security.md).

### "Lambda vs Cloudflare Workers para este caso?"

Lambda gana por integracion nativa con DynamoDB + SES. Workers
requiere rewrite en JS/TS + middleware adicional para hablar con AWS.
Comparacion completa en
[09-lambda-vs-alternatives.md](../../docs/aws-lambda/09-lambda-vs-alternatives.md).

### "El cold start es muy lento"

Diagnostico en [04-cold-start-optimization.md](../../docs/aws-lambda/04-cold-start-optimization.md).
Quick checks:
- arm64? (si no, switch a arm64 = -20% costo + cold start menor)
- boto3 client en module scope?
- Package size < 50MB? (`du -sh .aws-sam/build/*`)
- Memory >= 512MB? (mas memoria = mas CPU = init mas rapido)
- Imports pesados (pandas, numpy)? eliminar si no se usa

## Anti-patrones a evitar

- Responder desde training data sin leer la doc del proyecto
- Recomendar Python 3.11 o 3.12 (3.13 es el oficial actual)
- Sugerir x86_64 por default (arm64 es mejor opcion)
- Instanciar boto3 client dentro del handler (cold start hit)
- Hardcodear secrets en codigo o env vars
- Recomendar `dynamodb:*` o `ses:*` en IAM policies
- Pedir al usuario que "ponga Account Admin para simplificar"
- Sugerir CDK para 3 Lambdas (SAM es la herramienta correcta aqui)
- Olvidar X-Ray tracing en setup inicial (debugging en prod sin trace = pesadilla)

## Comandos utiles

```bash
# Validar template SAM
sam validate

# Build con container (evita issues binarios cross-platform)
sam build --use-container

# Deploy interactive
sam deploy --guided

# Invocar local con event sample
sam local invoke ContactFormFunction --event events/contact-post.json

# Levantar API Gateway local
sam local start-api --port 3000

# Logs tail real-time
sam logs -n ContactFormFunction --tail

# Verificar IAM con Access Analyzer
aws accessanalyzer list-findings --analyzer-arn <arn>
```

## Relacion con otras skills/rules

- `aws-api-gateway` — el trigger de contact-form y tracking-pixel
- `aws-dynamodb` — el storage que escriben contact-form y tracking-pixel
- `aws-ses` — el servicio de email que invoca contact-form
- `cloudflare-turnstile` — el servicio que valida contact-form (via `common/turnstile.py`)
- [.claude/rules/python.md](../../rules/python.md) — convenciones Python del proyecto
- [.claude/rules/security.md](../../rules/security.md) — secrets, IAM, encryption
- [.claude/rules/verify-before-done.md](../../rules/verify-before-done.md) — gates antes de deploy

## Cuando NO invocar esta skill

- Pregunta sobre Lambda en otro runtime (Node, Go, Rust)
- Pregunta sobre Lambda@Edge o CloudFront Functions (otra cosa)
- Pregunta sobre AWS Step Functions u orquestacion compleja (usar otro patron)
- Pregunta sobre EventBridge, SQS, SNS triggers (no aplican a este caso)
- Pregunta sobre Lambda en VPC (no aplica — el portfolio no necesita VPC)
