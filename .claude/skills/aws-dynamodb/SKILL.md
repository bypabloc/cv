---
name: aws-dynamodb
description: >
  AWS DynamoDB reference for this portfolio (us-west-2, 2 tables:
  contacts for form submissions ~200/mo, tracking for page views
  ~15000/mo with TTL 60 days). Covers On-Demand vs Provisioned capacity
  mode decision (On-Demand obvious for spiky bursty workload, free tier
  perpetual 25 WCU + 25 RCU + 25GB storage post-2024 still applies),
  single-table design pattern (Rick Houlihan / Alex DeBrie — documented
  as reference but NOT applied here because 2 separate decoupled
  domains), TTL on tracking table (Unix epoch seconds attribute,
  AWS deletes within 48h, ZERO WCU cost on delete = massive savings on
  rolling 60-day window), GSI cost trade-offs (double write
  amplification, sparse GSI patterns, when to use), boto3 Resource vs
  Client API (Resource recommended for CRUD), Decimal handling (DynamoDB
  uses Decimal, Python conversion gotcha), ConditionExpression for
  idempotent writes, scan vs query (NEVER full scan in production),
  AWS SAM template with TimeToLiveSpecification +
  PointInTimeRecoverySpecification + BillingMode PAY_PER_REQUEST,
  pricing 2026 us-west-2 ($1.25/M writes + $0.25/M reads + $0.25/GB-mo,
  total <$0.01/mo for this portfolio), IAM least privilege (PutItem
  scoped to specific table ARN, NEVER dynamodb:*), encryption at rest
  with AWS-owned key or customer KMS, NEVER expose DynamoDB direct to
  internet via Federated Identities — always Lambda intermediary.
  ALWAYS invoke this skill BEFORE answering ANY question about DynamoDB
  in this project, including questions framed as "nosql aws", "tabla
  dynamo", or "guardar datos en aws" without explicitly saying DynamoDB.
  NEVER answer from training data alone — this project has consolidated
  2026 knowledge (On-Demand as default post-Nov 2024 AWS recommendation,
  free tier perpetual breakdown, TTL exact behavior, IAM scoping
  patterns) that overrides generic advice.
  Use when the user says "dynamodb", "dynamo", "aws dynamo", "nosql aws",
  "tabla dynamo", "tabla dynamodb", "dynamodb table", "partition key",
  "sort key", "primary key dynamodb", "gsi", "global secondary index",
  "lsi", "local secondary index", "single-table design", "rick houlihan",
  "alex debrie", "ttl dynamodb", "expires_at dynamodb", "borrar
  automatico dynamodb", "auto delete dynamodb", "on-demand dynamodb",
  "pay-per-request", "provisioned dynamodb", "billing mode dynamodb",
  "boto3 dynamodb", "put_item python", "get_item python", "query
  dynamodb", "scan dynamodb", "no hagas scan", "conditional write
  dynamodb", "decimal dynamodb", "json dynamodb", "transaction dynamodb",
  "streams dynamodb", "point in time recovery", "pitr dynamodb",
  "global tables", "dynamodb backup", "dynamodb encryption", "kms
  dynamodb", "dynamodb iam", "least privilege dynamodb", "como guardo
  un form en aws", "donde guardo los datos del form", "donde guardo
  tracking", "que base usar para tracking", "free tier dynamodb",
  "precio dynamodb", "costo dynamodb", "dynamodb pricing".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash(aws:*), Bash(sam:*)
argument-hint: "tema: architecture | capacity | single-table | ttl | gsi | boto3 | deploy | cost | security"
metadata:
  version: "1.0"
---

# AWS DynamoDB — knowledge reference

> Conocimiento consolidado sobre DynamoDB para el portfolio (2 tablas en
> us-west-2 con On-Demand + TTL 60d en tracking). Toda decision, gotcha
> y pricing en `.claude/docs/aws-dynamodb/`.

## Pre-requisito OBLIGATORIO

Antes de responder, leer la doc relevante de `.claude/docs/aws-dynamodb/`:

| Tema de la pregunta | Archivo a leer |
|---------------------|----------------|
| Modelo NoSQL, PK/SK, atributos | [01-architecture.md](../../docs/aws-dynamodb/01-architecture.md) |
| On-Demand vs Provisioned | [02-capacity-modes.md](../../docs/aws-dynamodb/02-capacity-modes.md) |
| Single-table design (referencia, NO aplicado) | [03-single-table-design.md](../../docs/aws-dynamodb/03-single-table-design.md) |
| TTL en tracking (60d, costo $0) | [04-ttl-tracking.md](../../docs/aws-dynamodb/04-ttl-tracking.md) |
| GSI patterns (descartado para este caso) | [05-gsi-patterns.md](../../docs/aws-dynamodb/05-gsi-patterns.md) |
| boto3 Python (put_item, query, Decimal) | [06-boto3-python.md](../../docs/aws-dynamodb/06-boto3-python.md) |
| SAM template + deployment | [07-deployment-sam.md](../../docs/aws-dynamodb/07-deployment-sam.md) |
| Pricing 2026 + free tier | [08-cost-optimization.md](../../docs/aws-dynamodb/08-cost-optimization.md) |
| IAM least privilege + encryption | [09-security-best-practices.md](../../docs/aws-dynamodb/09-security-best-practices.md) |

## Reglas criticas (siempre activas)

1. **SIEMPRE** On-Demand (`BillingMode: PAY_PER_REQUEST`) para este
   portfolio. AWS recomienda como default post-Nov 2024 para workloads
   nuevos. Volumen bajo + spiky = NO provisioned capacity planning.

2. **SIEMPRE** TTL en tabla `tracking` con atributo `expires_at`
   (Number = Unix epoch seconds). AWS borra automaticamente en 48h
   post-expiration. ZERO costo de delete. Sin TTL = storage cost crece
   indefinidamente.

3. **NUNCA** single-table design en este portfolio. Documentado en
   [03-single-table-design.md](../../docs/aws-dynamodb/03-single-table-design.md)
   como referencia futura, pero 2 tablas (`contacts`, `tracking`) es
   correcto: dominios desacoplados, no hay queries cross-domain.

4. **NUNCA** `dynamodb:*` en IAM policies. Scope estricto:
   - contact-form Lambda → `dynamodb:PutItem` en `arn:aws:dynamodb:us-west-2:*:table/contacts`
   - tracking-pixel Lambda → `dynamodb:PutItem` en `arn:aws:dynamodb:us-west-2:*:table/tracking`
   - Sin read, sin delete, sin index, sin nada mas.

5. **NUNCA** `Scan` en codigo de produccion sin `FilterExpression`. Scan
   = full table read = costo proporcional a tamano de tabla. Solo
   usar para admin scripts puntuales.

6. **SIEMPRE** `boto3.resource('dynamodb')` (high-level Resource API),
   NO `boto3.client('dynamodb')` (low-level). Resource maneja
   serializacion Decimal/JSON automaticamente.

7. **SIEMPRE** Decimal para numeros, NUNCA float. DynamoDB no acepta
   `float('3.14')` directo. Codigo:
   ```python
   from decimal import Decimal
   table.put_item(Item={'amount': Decimal(str(amount))})
   ```

8. **SIEMPRE** `ConditionExpression` para writes que no deben
   sobreescribir. Ej: para evitar duplicate contact submissions:
   ```python
   table.put_item(
       Item={'id': contact_id, ...},
       ConditionExpression='attribute_not_exists(id)'
   )
   ```

9. **SIEMPRE** verificar la skill antes de modificarla con
   `claude --permission-mode bypassPermissions -p` (regla
   [.claude/rules/claude-config-testing.md](../../rules/claude-config-testing.md)).

## Workflow tipico de respuesta

1. Identificar el tema (modelo / capacity / TTL / boto3 / cost / etc.)
2. Leer doc relevante de `.claude/docs/aws-dynamodb/`
3. Responder con:
   - Codigo Python boto3 ejecutable
   - SAM YAML snippet si toca infra
   - Estimacion de costo us-west-2 Mayo 2026
4. Si la pregunta cae fuera de scope: derivar a otra skill

## Atajos rapidos

### "Como guardo el form de contacto en DynamoDB?"

Tabla `contacts` con PK = `id` (UUIDv7). Codigo en
[06-boto3-python.md](../../docs/aws-dynamodb/06-boto3-python.md):

```python
import boto3
from uuid import uuid4
from datetime import datetime, UTC

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('contacts')

def save_contact(payload: dict) -> str:
    contact_id = str(uuid4())
    table.put_item(Item={
        'id': contact_id,
        'email': payload['email'],
        'name': payload['name'],
        'message': payload['message'],
        'service_type': payload.get('service_type'),
        'created_at': datetime.now(UTC).isoformat(),
    })
    return contact_id
```

### "Como configuro TTL para borrar tracking despues de 60 dias?"

SAM template + atributo `expires_at`:

```yaml
TrackingTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: tracking
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: session_id
        AttributeType: S
      - AttributeName: page_id
        AttributeType: S
    KeySchema:
      - AttributeName: session_id
        KeyType: HASH
      - AttributeName: page_id
        KeyType: RANGE
    TimeToLiveSpecification:
      AttributeName: expires_at
      Enabled: true
```

```python
import time
expires_at = int(time.time()) + 60 * 24 * 3600  # 60 dias
table.put_item(Item={..., 'expires_at': expires_at})
```

Detalle en [04-ttl-tracking.md](../../docs/aws-dynamodb/04-ttl-tracking.md).

### "Cuanto va a costar?"

Para 200 contacts + 15000 tracking events/mes: **<$0.01/mes**. Free
tier on-demand: 25GB storage + 2.5M reads + 1M writes/mes (perpetuo).
Detalle en [08-cost-optimization.md](../../docs/aws-dynamodb/08-cost-optimization.md).

### "Necesito un GSI para buscar contactos por email?"

Probablemente no — el form de contacto es write-only desde Lambda. Si
en el futuro hay dashboard que liste por email, agregar GSI con
partition key `email`. Costo: 2x write amplification (~$0.0008/mes).
Detalle en [05-gsi-patterns.md](../../docs/aws-dynamodb/05-gsi-patterns.md).

### "DynamoDB vs PostgreSQL vs SQLite?"

DynamoDB gana para este caso: serverless (no manage), free tier
perpetuo, escala automatica, integracion native con Lambda. PostgreSQL
seria overkill ($15+/mes en RDS). SQLite no aplica (no hay server).
Detalle en [01-architecture.md](../../docs/aws-dynamodb/01-architecture.md).

## Anti-patrones a evitar

- Responder desde training data sin leer la doc del proyecto
- Recomendar Provisioned capacity para 200 items/mes
- Sugerir `Scan` para listar items (use Query con sort key)
- Hardcodear table names en codigo (usar env vars + SAM `!Ref`)
- Permitir DynamoDB directo desde browser via Cognito Federated Identities
- Olvidar TTL en tabla de tracking (storage cost growing)
- Usar `float` para numericos (DynamoDB requires Decimal)
- IAM policy con `dynamodb:*` "para evitar permission denied"
- Crear tablas sin Point-In-Time Recovery (PITR) en prod
- Single-table design forzado para 2 dominios desacoplados

## Comandos utiles

```bash
# Listar tablas
aws dynamodb list-tables --region us-west-2

# Describir tabla
aws dynamodb describe-table --table-name contacts --region us-west-2

# Insert item manualmente (debugging)
aws dynamodb put-item --table-name contacts \
  --item '{"id":{"S":"test-id"},"email":{"S":"test@example.com"}}' \
  --region us-west-2

# Verificar TTL config
aws dynamodb describe-time-to-live --table-name tracking --region us-west-2

# Item count (cuidado, es eventual y puede tardar)
aws dynamodb describe-table --table-name tracking \
  --query 'Table.ItemCount' --region us-west-2
```

## Relacion con otras skills/rules

- `aws-lambda-python` — los handlers que escriben a DynamoDB
- `aws-api-gateway` — el trigger upstream
- `aws-ses` — el otro destino del form contacto (email + DB)
- [.claude/rules/python.md](../../rules/python.md) — convenciones Python
- [.claude/rules/security.md](../../rules/security.md) — IAM, encryption
- [.claude/rules/verify-before-done.md](../../rules/verify-before-done.md)

## Cuando NO invocar esta skill

- Pregunta sobre RDS PostgreSQL / Aurora (otro servicio AWS)
- Pregunta sobre Redis / ElastiCache (cache layer, no DynamoDB)
- Pregunta sobre Elasticsearch / OpenSearch (search, no key-value)
- Pregunta sobre S3 (object storage, no DB)
- Pregunta sobre Neptune o DocumentDB (graph / mongo-compat)
- Pregunta sobre Prisma u otro ORM (otros stacks, no DynamoDB)
