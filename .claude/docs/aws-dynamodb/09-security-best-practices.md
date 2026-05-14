# Security Best Practices

> IAM least privilege, encryption, protecciones contra abuse. Produccion-ready.

## 1. IAM Least Privilege

NUNCA usar `dynamodb:*`. Cada Lambda function solo lo que necesita.

### Contact Form Handler (solo PutItem en contacts)

```yaml
ContactFormRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action: sts:AssumeRole
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    Policies:
      - PolicyName: ContactsTableAccess
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - dynamodb:PutItem
              Resource: !GetAtt ContactsTable.Arn
              Condition:
                StringEquals:
                  'dynamodb:LeadingKeys': ['${aws:username}']
```

### Tracking Pixel Handler (solo PutItem en tracking)

```yaml
TrackingPixelRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action: sts:AssumeRole
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    Policies:
      - PolicyName: TrackingTableAccess
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - dynamodb:PutItem
              Resource: !GetAtt TrackingTable.Arn
```

### Admin Dashboard (Query + GetItem)

```yaml
AdminDashboardRole:
  Type: AWS::IAM::Role
  Properties:
    Policies:
      - PolicyName: QueryContactsTracking
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - dynamodb:Query
                - dynamodb:GetItem
                - dynamodb:Scan  # Solo si necesario (preferir Query)
              Resource:
                - !GetAtt ContactsTable.Arn
                - !GetAtt TrackingTable.Arn
              # IMPORTANTE: Restringir a horario administrativo
              Condition:
                DateGreaterThan:
                  'aws:CurrentTime': '2026-01-01T00:00:00Z'
                DateLessThan:
                  'aws:CurrentTime': '2099-12-31T23:59:59Z'
```

## 2. Encryption

### At Rest (Storage)

DynamoDB **encryption by default** con AWS-owned keys (sin costo).

**Customer-managed KMS (si requiere compliance):**

```yaml
DynamoDBKMSKey:
  Type: AWS::KMS::Key
  Properties:
    Description: KMS key para DynamoDB encryption
    KeyPolicy:
      Version: '2012-10-17'
      Statement:
        - Sid: Enable IAM policies
          Effect: Allow
          Principal:
            AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
          Action: 'kms:*'
          Resource: '*'
        - Sid: Allow DynamoDB
          Effect: Allow
          Principal:
            Service: dynamodb.amazonaws.com
          Action:
            - 'kms:Decrypt'
            - 'kms:GenerateDataKey'
          Resource: '*'

ContactsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    SSESpecification:
      SSEEnabled: true
      SSEType: KMS
      KMSMasterKeyId: !GetAtt DynamoDBKMSKey.Arn
    # ...
```

**Costo:** $1/mes por key + $0.03 per 10000 requests (para este caso: +$1/mes).

### In Transit

Lambda → DynamoDB usa HTTPS obligatoriamente (AWS internal). No hay exposición.

**NUNCA** exponer DynamoDB directo a internet (sin Lambda proxy).

## 3. Validacion de Input

En Lambda, validar ANTES de DynamoDB:

```python
import json
from jsonschema import validate, ValidationError

CONTACT_SCHEMA = {
    'type': 'object',
    'properties': {
        'email': {'type': 'string', 'format': 'email', 'maxLength': 255},
        'name': {'type': 'string', 'minLength': 1, 'maxLength': 100},
        'message': {'type': 'string', 'minLength': 10, 'maxLength': 2000},
        'service_type': {
            'enum': ['generic', 'fintech', 'architect', 'leader', 'vibe']
        },
        'budget': {'type': 'number', 'minimum': 0, 'maximum': 1000000},
    },
    'required': ['email', 'name', 'message'],
    'additionalProperties': False,
}

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        validate(instance=body, schema=CONTACT_SCHEMA)
        # Safe to write to DB
        # ...
    except ValidationError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': e.message}),
        }
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON'}),
        }
```

## 4. Protecciones contra Abuse

### Rate Limiting en Lambda

```python
from functools import wraps
from time import time
from collections import defaultdict

# Simple in-memory rate limiter (reset on redeploy)
requests_per_ip = defaultdict(list)
MAX_REQUESTS = 10
WINDOW_SECONDS = 3600  # 1 hour

def rate_limit(handler):
    @wraps(handler)
    def wrapper(event, context):
        ip = event['requestContext']['identity']['sourceIp']
        now = time()
        
        # Cleanup old requests
        requests_per_ip[ip] = [t for t in requests_per_ip[ip] if now - t < WINDOW_SECONDS]
        
        if len(requests_per_ip[ip]) >= MAX_REQUESTS:
            return {
                'statusCode': 429,
                'body': json.dumps({'error': 'Too many requests'}),
            }
        
        requests_per_ip[ip].append(now)
        return handler(event, context)
    
    return wrapper

@rate_limit
def lambda_handler(event, context):
    # ...
```

### CloudFront WAF (si integrado)

En Cloudflare (frontend del portfolio), bloquear IPs suspicious:

```
(cf.threat_score > 50) or (cf.bot_score < 30) → Challenge
```

## 5. Point-in-Time Recovery (PITR)

Habilitar para recuperacion ante borrados accidentales:

```yaml
ContactsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    PointInTimeRecoverySpecification:
      PointInTimeRecoveryEnabled: true  # Cuesta $0.20/GB/mes
```

**Que restaura:**
- Restores a cualquier punto en los últimos 35 dias
- No incluye deletes realizados por TTL
- Crea tabla nueva, no sobrescribe original

```bash
aws dynamodb restore-table-to-point-in-time \
  --source-table-name portfolio-dev-contacts \
  --target-table-name portfolio-dev-contacts-restore \
  --restore-date-time 2026-05-10T14:30:00Z \
  --region us-west-2
```

## 6. Monitoring y Logging

### CloudWatch Logs

```yaml
ContactFormFunction:
  Type: AWS::Serverless::Function
  Properties:
    # ...
    Tracing: Active  # Enable X-Ray tracing
    Environment:
      Variables:
        LOG_LEVEL: INFO
```

### CloudTrail (Auditing)

Registra QUIEN hizo QUE en DynamoDB:

```yaml
DynamoDBTrail:
  Type: AWS::CloudTrail::Trail
  Properties:
    S3BucketName: !Ref AuditBucket
    IncludeGlobalServiceEvents: true
    IsLogging: true
    EventSelectors:
      - IncludeManagementEvents: false
        DataResources:
          - Type: 'AWS::DynamoDB::Table'
            Values:
              - !Sub '${ContactsTable.Arn}'
              - !Sub '${TrackingTable.Arn}'
```

### Alertas de Anomalias

```yaml
DeleteAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: UserErrors
    Namespace: AWS/DynamoDB
    Statistic: Sum
    Period: 300
    Threshold: 5  # 5+ deletes en 5 min = sospechoso
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref SecurityTeamTopic
```

## 7. Anti-Patterns Prohibidos

| Pattern | Problema | Alternativa |
|---------|----------|------------|
| **DynamoDB directo desde browser** | Expone AWS credentials | Usar Lambda proxy |
| **Hardcodear table names en codigo** | Inflexible, secrets en repo | Variables de entorno SAM |
| **Sin validacion de input** | Inyeccion de datos | jsonschema validation |
| **Scan sin filter** | Costoso, lento | Query con PK + SK |
| **TTL como unica proteccion** | 48h delay antes de borrado | Agregar explicit delete si sensible |
| **Global Table sin encryption** | Replicacion sin seguridad | Habilitar KMS en todas regiones |

## 8. Compliance (GDPR, CCPA, etc.)

### Right to Deletion

Si usuario solicita borrado (GDPR article 17):

```python
def delete_contact(contact_id):
    """Borrar contacto y sus tracking events."""
    # 1. Borrar item de contacts
    contacts_table.delete_item(Key={'id': contact_id})
    
    # 2. Opcional: Borrar eventos relacionados (si hay FK)
    # (No aplica en este diseño, son tablas desacopladas)
```

### Data Exporting

Si usuario solicita export (GDPR article 15):

```python
def export_user_data(email):
    """Retornar todos los datos de un usuario."""
    # Query contacts
    response = contacts_table.scan(
        FilterExpression=Attr('email').eq(email)
    )
    items = response.get('Items', [])
    
    # Retornar como JSON
    return json.dumps(items, default=str, indent=2)
```

## Paso Siguiente

- Deployment: [07-deployment-sam.md](07-deployment-sam.md)
- Costos: [08-cost-optimization.md](08-cost-optimization.md)
