# Backend serverless del portfolio

> Backend del form de contacto y el tracking de eventos del portfolio:
> 4 Lambdas Python 3.13 (arm64) en `us-east-1`. devtools provisiona cada
> recurso (tablas DynamoDB, API Gateway, DLQ SQS) y cada Lambda con AWS
> CLI directo, manteniendo el estado en archivos locales — sin SAM ni
> CloudFormation. API Gateway REST + DynamoDB + SES + Neon PostgreSQL.
> Costo ~$0/mes (free tier perpetuo, sin WAF, sin alarmas).

## Tabla de contenidos

| Capitulo | Cuando leer |
|----------|-------------|
| [01-arquitectura-5-stacks.md](01-arquitectura-5-stacks.md) | Entender el modelo: recursos compartidos + 4 Lambdas provisionados con AWS CLI, la publicacion a SSM, la estructura de carpetas y los Lambdas |
| [02-flujos.md](02-flujos.md) | Ver los diagramas de flujo de cada Lambda: `contact_form` (POST /contact), `tracking_pixel` (POST /track), `stream_processor` (Streams -> Neon), `db` |
| [03-datos.md](03-datos.md) | Esquema de las 5 tablas DynamoDB y de las tablas Neon PostgreSQL replicadas; que dato vive donde |
| [04-deploy-operacion.md](04-deploy-operacion.md) | Deployar (recursos primero, luego cada Lambda), comandos devtools, rotar secrets, troubleshooting |
| [05-estado-local.md](05-estado-local.md) | El archivo de estado de devtools: esquema, donde vive, gitignore, comandos `status` y `destroy` |

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** los recursos compartidos se provisionan ANTES que los
  Lambdas: los 4 Lambdas resuelven los identificadores de los recursos
  via SSM. `serverless provision-infra` provisiona todos los recursos.
- **SIEMPRE** cada Lambda se opera con `python devtools/run.py serverless
  <cmd> --lambda=<nombre>` (formato `lambda-controller`); el nombre corto
  se resuelve contra `serverless/lambda/services/<nombre>/`.
- **SIEMPRE** el `manifest.yaml` de cada Lambda es la fuente de verdad de
  su config; devtools lo lee directamente para provisionarlo con AWS CLI.
- **SIEMPRE** Python 3.13 (managed runtime), arm64 Graviton2, Powertools v3.
- **SIEMPRE** secrets via SSM Parameter Store + KMS, NUNCA env vars planos.
- **NUNCA** editar ni commitear `build/`, `build.zip` ni el archivo de
  estado de devtools (`serverless/lambda/.state/`) — son efimeros /
  locales, generados por devtools.
- **NUNCA** modificar un recurso AWS a mano en la consola — devtools no
  detecta el drift; cambiar el manifiesto y re-deployar. Auditar con
  `serverless status`.
- **NUNCA** atribucion de IA en codigo, commits ni docstrings.

## Modelo en una tabla

| Recurso | Contenido | Operacion |
|---------|-----------|-----------|
| Tablas DynamoDB | `contacts`, `tracking`, `cache`, `rate-limit-rules`, `rate-limit-buckets` | `serverless provision-infra` (todas) |
| API Gateway REST | API REST regional (sin metodos) | `serverless provision-infra` |
| DLQ SQS | DLQ del `stream_processor` | `serverless provision-infra` |
| Lambda `db` | schema Alembic, invoke directo | `serverless deploy --lambda=db` |
| Lambda `contact_form` | `POST /contact` | `serverless deploy --lambda=contact_form` |
| Lambda `tracking_pixel` | `POST /track` | `serverless deploy --lambda=tracking_pixel` |
| Lambda `stream_processor` | Event Source Mappings de los Streams | `serverless deploy --lambda=stream_processor` |

`serverless provision-infra` provisiona en orden los 7 recursos
compartidos (5 tablas + API + DLQ) con AWS CLI directo y publica sus
identificadores a SSM. `serverless list-resources` lista los recursos
declarados en `resources/`.

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
