# Backend serverless del portfolio

> Backend del form de contacto y el tracking de eventos del portfolio:
> 4 Lambdas Python 3.13 (arm64) en `us-east-1`. Cada recurso compartido
> (tablas DynamoDB, API Gateway, DLQ SQS) es un stack CloudFormation
> autonomo; cada Lambda es otro stack. API Gateway REST + DynamoDB + SES
> + Neon PostgreSQL. Costo ~$0/mes (free tier perpetuo, sin WAF, sin
> alarmas).

## Tabla de contenidos

| Capitulo | Cuando leer |
|----------|-------------|
| [01-arquitectura-5-stacks.md](01-arquitectura-5-stacks.md) | Entender el modelo de stacks: N stacks de recurso autonomos + 4 stacks de Lambda, la publicacion a SSM, la estructura de carpetas y los Lambdas |
| [02-flujos.md](02-flujos.md) | Ver los diagramas de flujo de cada Lambda: `contact_form` (POST /contact), `tracking_pixel` (POST /track), `stream_processor` (Streams -> Neon), `db` |
| [03-datos.md](03-datos.md) | Esquema de las 5 tablas DynamoDB y de las tablas Neon PostgreSQL replicadas; que dato vive donde |
| [04-deploy-operacion.md](04-deploy-operacion.md) | Deployar (recursos primero, luego cada Lambda), comandos devtools, rotar secrets, troubleshooting |

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** los stacks de recurso (`portfolio-<tipo>-<nombre>-<stage>`)
  se deployan ANTES que los stacks de Lambda: los 4 Lambdas resuelven los
  identificadores de los recursos via SSM. `serverless deploy-infra`
  deploya todos los stacks de recurso.
- **SIEMPRE** cada Lambda se opera con `python devtools/run.py serverless
  <cmd> --lambda=<nombre>` (formato `lambda-controller`); el nombre corto
  se resuelve contra `serverless/lambda/services/<nombre>/`.
- **SIEMPRE** el `lambda.yaml` de cada Lambda es la fuente de verdad de
  su config; el `template.yaml` SAM se genera y es efimero (`.gitignore`).
- **SIEMPRE** Python 3.13 (managed runtime), arm64 Graviton2, Powertools v3.
- **SIEMPRE** secrets via SSM Parameter Store + KMS, NUNCA env vars planos.
- **NUNCA** editar ni commitear `template.yaml`, `build/` ni
  `build/core/shared/` (todos efimeros, generados por devtools antes de
  cada `run`/`deploy`).
- **NUNCA** existe ya un stack de infra monolitico — cada recurso es su
  propio stack y publica sus identificadores a SSM (no usa `Export`/
  `Fn::ImportValue`).
- **NUNCA** atribucion de IA en codigo, commits ni docstrings.

## Modelo en una tabla

| Stack | Contenido | Operacion |
|-------|-----------|-----------|
| `portfolio-dynamodb-<nombre>-<stage>` | una tabla DynamoDB (`contacts`, `tracking`, `cache`, `rate-limit-rules`, `rate-limit-buckets`) | `serverless deploy-resource --name=dynamodb/<nombre>` |
| `portfolio-api_gateway-portfolio-api-<stage>` | API Gateway REST (sin metodos) | `serverless deploy-resource --name=api_gateway/portfolio-api` |
| `portfolio-sqs-stream-processor-dlq-<stage>` | DLQ del `stream_processor` | `serverless deploy-resource --name=sqs/stream-processor-dlq` |
| `portfolio-db-<stage>` | Lambda `db` (schema Alembic, invoke directo) | `serverless deploy --lambda=db` |
| `portfolio-contact-form-<stage>` | Lambda `contact_form` + `POST /contact` | `serverless deploy --lambda=contact_form` |
| `portfolio-tracking-pixel-<stage>` | Lambda `tracking_pixel` + `POST /track` | `serverless deploy --lambda=tracking_pixel` |
| `portfolio-stream-processor-<stage>` | Lambda `stream_processor` + Event Source Mappings | `serverless deploy --lambda=stream_processor` |

`serverless deploy-infra` deploya en orden los 7 stacks de recurso (5
tablas + API + DLQ); cada uno tambien se deploya por separado con
`deploy-resource`.

## Que NO esta aqui (referencias)

Este doc cubre lo ESPECIFICO del backend del portfolio. Para los temas
transversales, consultar la fuente correspondiente:

| Tema | Fuente |
|------|--------|
| Formato `lambda-controller` (estructura `core/`, `operation+action`, controllers/services, testing) | [.claude/rules/lambda-controller.md](../../rules/lambda-controller.md) + [.claude/docs/lambda-controller/](../lambda-controller/) o skill `lambda-controller` |
| Runtime Lambda, Powertools, cold start, IAM, costos | skill `aws-lambda-python` |
| REST API, throttling, request validators, CORS | skill `aws-api-gateway` |
| DynamoDB On-Demand, TTL, boto3, pricing | skill `aws-dynamodb` |
| Email transaccional, DKIM/SPF/DMARC | skill `aws-ses` |
| Cloudflare Turnstile (captcha, siteverify) | skill `cloudflare-turnstile` |
| Neon serverless PostgreSQL | skill `neon` + [.claude/rules/neon-management.md](../../rules/neon-management.md) |
| Rate-limit per-IP con DynamoDB (sin WAF) | skill `serverless-rate-limit` |
| Cache con DynamoDB TTL | skill `dynamodb-cache` |
| Schema PostgreSQL unificado (modelos SQLAlchemy + Alembic) | `serverless/lambda/shared/db/` + [docs/diagrams/db-er.mmd](../../../docs/diagrams/db-er.mmd) |
| Inventario de secrets SSM | [.claude/rules/serverless-secrets.md](../../rules/serverless-secrets.md) |

## Navegacion

- [.claude/docs/ (knowledge base)](..)
- [.claude/rules/lambda-controller.md](../../rules/lambda-controller.md)
- [01-arquitectura-5-stacks.md](01-arquitectura-5-stacks.md)
