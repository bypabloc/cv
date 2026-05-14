---
title: Schema DynamoDB - rate_limit_rules y rate_limit_buckets
description: Design de 2 tablas On-Demand, SAM template, IAM least privilege.
status: stable
last-reviewed: 2026-05-14
---

# 03. Schema Design - DynamoDB Tables

> Design de las 2 tablas DynamoDB: `rate_limit_rules` (config) y
> `rate_limit_buckets` (contadores). SAM template + IAM least privilege.

[← Deep dive](./02-sliding-window-weighted-deep-dive.md) | [README](./README.md) | [Siguiente: Implementacion Python →](./04-python-implementation.md)

## Tabla 1: `rate_limit_rules` (Configuracion)

Almacena las reglas de rate-limit: limites por endpoint, IP whitelist, blacklist, country rules.

### Schema

| Campo | Tipo | Descripcion | Ejemplo |
|-------|------|-------------|---------|
| `rule_key` (PK) | String | Clave unica. Formato: `endpoint#/contact` \| `ip#whitelist#X.X.X.X` \| `ip#blacklist#X.X.X.X` \| `country#US` | `endpoint#/contact` |
| `kind` | String (enum) | Tipo de regla: `endpoint`, `ip_whitelist`, `ip_blacklist`, `country_block` | `endpoint` |
| `limit` | Number | Max requests en ventana (si kind=endpoint) | 3 |
| `window_seconds` | Number | Duracion ventana (segundos) | 60 |
| `action` | String (enum) | Accion si se excede: `BLOCK`, `THROTTLE`, `CHALLENGE` | `BLOCK` |
| `expires_at` | Number (Unix timestamp, optional) | Si presente, item expira (TTL para blacklist temporal) | 1715678400 |
| `created_at` | String (ISO 8601) | Timestamp creacion | `2026-05-14T10:30:00Z` |
| `created_by` | String | Admin que creo la regla (para audit) | `admin@portfolio.com` |
| `reason` | String (optional) | Motivo de la regla (blacklist: "bot", whitelist: "partner") | `"Detected 3 tokens in 60s"` |
| `ttl_hours` | Number (optional) | Si automatico, cuanto tiempo antes de expirar | 24 |

### Ejemplos de items

```json
{
  "rule_key": "endpoint#/contact",
  "kind": "endpoint",
  "limit": 3,
  "window_seconds": 60,
  "action": "BLOCK",
  "created_at": "2026-05-14T00:00:00Z",
  "created_by": "admin"
}

{
  "rule_key": "ip#whitelist#203.0.113.1",
  "kind": "ip_whitelist",
  "created_at": "2026-05-14T00:00:00Z",
  "created_by": "admin",
  "reason": "Pablo personal IP"
}

{
  "rule_key": "ip#blacklist#198.51.100.42",
  "kind": "ip_blacklist",
  "expires_at": 1715678400,
  "created_at": "2026-05-14T08:00:00Z",
  "created_by": "auto_blacklist",
  "reason": "Detected 3 tokens in 60s (bot)",
  "ttl_hours": 24
}

{
  "rule_key": "country#CN",
  "kind": "country_block",
  "created_at": "2026-05-14T00:00:00Z",
  "created_by": "admin",
  "reason": "High volume attack from China"
}
```

### Indice

- **PK**: `rule_key` (String)
- **No SK** (tabla simple, items cortos)
- **TTL**: Attribute `expires_at` (auto-delete de blacklist temporal)
- **No GSI** (queries son por `rule_key` exacto)

## Tabla 2: `rate_limit_buckets` (Contadores)

Almacena contadores sliding window por (IP + endpoint + window_start).

### Schema

| Campo | Tipo | Descripcion | Ejemplo |
|-------|------|-------------|---------|
| `bucket_key` (PK) | String | Clave unica. Formato: `<ip>#<endpoint>#<window_start>` | `203.0.113.1#/contact#1715670600` |
| `current_count` | Number | Requests en ventana actual | 2 |
| `current_window_start` | Number (Unix ts) | Timestamp inicio ventana actual | 1715670600 |
| `window_seconds` | Number | Duracion ventana (heredado de rules, pero cacheable) | 60 |
| `previous_count` | Number | Requests en ventana anterior (para weighted) | 1 |
| `previous_window_start` | Number (Unix ts) | Timestamp inicio ventana anterior | 1715670540 |
| `first_request` | Number (Unix ts) | Timestamp primer request en ventana actual | 1715670602 |
| `last_request` | Number (Unix ts) | Timestamp ultimo request | 1715670615 |
| `turnstile_tokens` | Number (optional) | Count de tokens Turnstile validos en ventana (para auto-blacklist) | 2 |
| `expires_at` | Number (Unix timestamp, TTL) | TTL: ventana expira despues (window_seconds * 2) | 1715670720 |

### Ejemplos de items

```json
{
  "bucket_key": "203.0.113.1#/contact#1715670600",
  "current_count": 2,
  "current_window_start": 1715670600,
  "window_seconds": 60,
  "previous_count": 1,
  "previous_window_start": 1715670540,
  "first_request": 1715670602,
  "last_request": 1715670615,
  "turnstile_tokens": 0,
  "expires_at": 1715670720
}

{
  "bucket_key": "198.51.100.99#/track#1715670600",
  "current_count": 15,
  "current_window_start": 1715670600,
  "window_seconds": 60,
  "previous_count": 20,
  "previous_window_start": 1715670540,
  "first_request": 1715670601,
  "last_request": 1715670659,
  "turnstile_tokens": 0,
  "expires_at": 1715670720
}
```

### Indice

- **PK**: `bucket_key` (String)
- **No SK** (tabla simple)
- **TTL**: Attribute `expires_at` (auto-delete after window expires)
- **No GSI** (queries por `bucket_key` exacto)

### Estimacion de items

```
100 requests/min = 6k/hora = 144k/dia

Si promedio 10 IPs unicas/min + 3 endpoints:
  ~30 buckets/min = 1800/hora = ~30k items/dia

Con TTL = window_seconds * 2 = 120s:
  Items vivos en DynamoDB: ~30k items (60s ventana * 2)
  Storage: ~200 bytes * 30k = 6 MB (muy dentro de free tier 25GB)
```

## SAM Template

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Rate-limiting serverless con DynamoDB para portfolio

Parameters:
  Environment:
    Type: String
    Default: prod
    AllowedValues: [dev, prod]

Resources:
  # ===== Tabla 1: Reglas =====
  RateLimitRulesTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub 'rate_limit_rules-${Environment}'
      BillingMode: PAY_PER_REQUEST  # On-Demand (siempre)
      AttributeDefinitions:
        - AttributeName: rule_key
          AttributeType: S
      KeySchema:
        - AttributeName: rule_key
          KeyType: HASH
      TimeToLiveSpecification:
        AttributeName: expires_at
        Enabled: true
      StreamSpecification:  # Opcional: para analytics
        StreamViewType: NEW_AND_OLD_IMAGES
      Tags:
        - Key: Purpose
          Value: rate-limiting-rules
        - Key: Environment
          Value: !Ref Environment

  # ===== Tabla 2: Buckets (contadores) =====
  RateLimitBucketsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub 'rate_limit_buckets-${Environment}'
      BillingMode: PAY_PER_REQUEST  # On-Demand (siempre)
      AttributeDefinitions:
        - AttributeName: bucket_key
          AttributeType: S
      KeySchema:
        - AttributeName: bucket_key
          KeyType: HASH
      TimeToLiveSpecification:
        AttributeName: expires_at
        Enabled: true
      PointInTimeRecoverySpecification:  # Opcional: backup automatico
        PointInTimeRecoveryEnabled: false
      Tags:
        - Key: Purpose
          Value: rate-limiting-buckets
        - Key: Environment
          Value: !Ref Environment

  # ===== IAM Role para Lambdas =====
  RateLimitLambdaRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub 'rate-limit-lambda-role-${Environment}'
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
        - PolicyName: DynamoDBRateLimitAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              # Read rules
              - Effect: Allow
                Action:
                  - dynamodb:GetItem
                Resource:
                  - !GetAtt RateLimitRulesTable.Arn
              # Read + Update buckets (para incrementar contador)
              - Effect: Allow
                Action:
                  - dynamodb:GetItem
                  - dynamodb:UpdateItem
                Resource:
                  - !GetAtt RateLimitBucketsTable.Arn

  # ===== Ejemplo: Lambda contact_form =====
  ContactFormFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub 'contact-form-${Environment}'
      Runtime: python3.13
      Handler: functions/contact.handler
      CodeUri: functions/
      Architectures: [arm64]
      Environment:
        Variables:
          RATE_LIMIT_RULES_TABLE: !Ref RateLimitRulesTable
          RATE_LIMIT_BUCKETS_TABLE: !Ref RateLimitBucketsTable
          ENVIRONMENT: !Ref Environment
      Role: !GetAtt RateLimitLambdaRole.Arn
      ReservedConcurrentExecutions: 5  # CRITICO: low concurrency para evitar DDoS
      Timeout: 15
      MemorySize: 512
      Events:
        ContactApi:
          Type: Api
          Properties:
            Path: /contact
            Method: POST
            RestApiId: !Ref PortfolioApi

  # ===== Ejemplo: Lambda track =====
  TrackFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub 'track-${Environment}'
      Runtime: python3.13
      Handler: functions/track.handler
      CodeUri: functions/
      Architectures: [arm64]
      Environment:
        Variables:
          RATE_LIMIT_RULES_TABLE: !Ref RateLimitRulesTable
          RATE_LIMIT_BUCKETS_TABLE: !Ref RateLimitBucketsTable
          ENVIRONMENT: !Ref Environment
      Role: !GetAtt RateLimitLambdaRole.Arn
      ReservedConcurrentExecutions: 10
      Timeout: 10
      MemorySize: 256
      Events:
        TrackApi:
          Type: Api
          Properties:
            Path: /track
            Method: POST
            RestApiId: !Ref PortfolioApi

  # ===== API Gateway =====
  PortfolioApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Environment
      Name: portfolio-api
      TracingEnabled: true

Outputs:
  RateLimitRulesTableName:
    Value: !Ref RateLimitRulesTable
    Description: Nombre de tabla de reglas
  
  RateLimitBucketsTableName:
    Value: !Ref RateLimitBucketsTable
    Description: Nombre de tabla de buckets
  
  LambdaRoleArn:
    Value: !GetAtt RateLimitLambdaRole.Arn
    Description: ARN de IAM role para Lambdas
```

## Despliegue

```bash
# Build
sam build

# Desplegar a us-west-2
sam deploy \
  --stack-name portfolio-rate-limit-prod \
  --region us-west-2 \
  --parameter-overrides Environment=prod

# Verificar tablas creadas
aws dynamodb list-tables --region us-west-2

# Ver detalles
aws dynamodb describe-table \
  --table-name rate_limit_rules-prod \
  --region us-west-2
```

## IAM Least Privilege (CRITICO)

Role `RateLimitLambdaRole` tiene SOLO:
- `dynamodb:GetItem` en tabla `rate_limit_rules`
- `dynamodb:GetItem` + `dynamodb:UpdateItem` en tabla `rate_limit_buckets`

**Prohibido**:
- NO Scan, Query, Delete (costosos / peligrosos)
- NO acceso a otras tablas
- NO IAM mutations

Esto sigue **least privilege principle**: cada Lambda solo puede hacer lo minimo
necesario.

---

**Verificado a**: 2026-05-14 (AWS SAM docs, DynamoDB On-Demand pricing)

**Fuentes**:
- [AWS SAM: DynamoDB Table Resource](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-dynamodbtable.html)
- [AWS DynamoDB: On-Demand billing](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-pricing.html)
