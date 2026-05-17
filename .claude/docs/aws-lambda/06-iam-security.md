# IAM: least privilege + secret management

> Roles y policies estrictas por Lambda, Secrets Manager, SSM Parameters,
> KMS encryption, VPC (no recomendado para este caso).

[← Anterior: Deployment SAM](./05-deployment-sam.md) | [Siguiente: Observability →](./07-observability.md)

## Principio: least privilege

NUNCA usar:
- `AmazonDynamoDBFullAccess`
- `AmazonSESFullAccess`
- `AdministratorAccess`

Usar policies inline con permisos **exactos necesarios**.

```yaml
ContactFormFunction:
  Type: AWS::Serverless::Function
  Properties:
    Policies:
      # Policy 1: DynamoDB (solo write a tabla contacts)
      - Statement:
          - Effect: Allow
            Action:
              - dynamodb:PutItem
            Resource: !GetAtt ContactsTable.Arn
      
      # Policy 2: SES (solo send email, solo desde verified sender)
      - Statement:
          - Effect: Allow
            Action:
              - ses:SendEmail
            Resource: !Sub 'arn:aws:ses:${AWS::Region}:${AWS::AccountId}:identity/${SenderEmail}'
      
      # Policy 3: SSM (solo GetParameter, solo Turnstile secret)
      - Statement:
          - Effect: Allow
            Action:
              - ssm:GetParameter
            Resource: !Sub 'arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/portfolio/turnstile-*'
      
      # Policy 4: KMS (solo decrypt)
      - Statement:
          - Effect: Allow
            Action:
              - kms:Decrypt
            Resource: !GetAtt KmsKey.Arn
```

## Por Lambda: permisos exactos

### contact-form

Necesita:
- DynamoDB: PutItem a tabla `contacts`
- SES: SendEmail como verified sender
- SSM: GetParameter para Turnstile (encrypted con KMS)

```yaml
ContactFormFunction:
  Policies:
    - Statement:
        - Effect: Allow
          Action: dynamodb:PutItem
          Resource: !GetAtt ContactsTable.Arn
    
    - Statement:
        - Effect: Allow
          Action: ses:SendEmail
          Resource: !Sub 'arn:aws:ses:${AWS::Region}:${AWS::AccountId}:identity/${SenderEmail}'
    
    - Statement:
        - Effect: Allow
          Action: ssm:GetParameter
          Resource: !Sub 'arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/portfolio/turnstile-*'
    
    - Statement:
        - Effect: Allow
          Action: kms:Decrypt
          Resource: !Ref KmsKey.Arn
```

### tracking-pixel

Necesita SOLO:
- DynamoDB: PutItem a tabla `tracking`

```yaml
TrackingPixelFunction:
  Policies:
    - Statement:
        - Effect: Allow
          Action: dynamodb:PutItem
          Resource: !GetAtt TrackingPixelTable.Arn
```

## Secrets Manager vs SSM Parameters

| Aspecto | Secrets Manager | SSM Parameter Store |
|---------|-----------------|---------------------|
| Pricing | $0.40/secret/mes | Free (estándar) |
| Rotation | Nativo con Lambda | Manual |
| Access patterns | GetSecretValue | GetParameter |
| Use case | API keys, DB pwd | Config, auth tokens |

**Para Turnstile**: SSM Parameter Store (bajo costo, simple).

```yaml
TurnstileParam:
  Type: AWS::SSM::Parameter
  Properties:
    Name: /portfolio/turnstile-key
    Type: SecureString
    Description: Cloudflare Turnstile key
    # Valor poblado via AWS CLI post-deployment
```

Crear via CLI (secure input):

```bash
# Guardar en env var desde archivo protegido
TURNSTILE=$(cat ~/.aws/credentials/turnstile.txt)

aws ssm put-parameter \
  --name /portfolio/turnstile-key \
  --type SecureString \
  --value "$TURNSTILE" \
  --key-id alias/portfolio-lambdas \
  --region us-east-1

# Limpiar
unset TURNSTILE
```

Acceso en handler:

```python
import boto3

ssm = boto3.client('ssm')

def get_turnstile_key():
    response = ssm.get_parameter(
        Name='/portfolio/turnstile-key',
        WithDecryption=True
    )
    return response['Parameter']['Value']

def validate_token(token):
    key = get_turnstile_key()
    # HTTP POST a Cloudflare siteverify
```

## KMS encryption

Encryptar secretos con KMS:

```yaml
KmsKey:
  Type: AWS::KMS::Key
  Properties:
    Description: Portfolio Lambda key
    KeyPolicy:
      Version: '2012-10-17'
      Statement:
        - Sid: Root manage
          Effect: Allow
          Principal:
            AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
          Action: 'kms:*'
          Resource: '*'
        
        - Sid: Lambda decrypt
          Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action:
            - 'kms:Decrypt'
            - 'kms:DescribeKey'
          Resource: '*'

KmsAlias:
  Type: AWS::KMS::Alias
  Properties:
    AliasName: alias/portfolio-lambdas
    TargetKeyId: !Ref KmsKey
```

## Caching de secrets

Evitar repeated KMS decrypts:

```python
import boto3
from functools import lru_cache

ssm = boto3.client('ssm')

@lru_cache(maxsize=1)
def get_turnstile_key():
    response = ssm.get_parameter(
        Name='/portfolio/turnstile-key',
        WithDecryption=True
    )
    return response['Parameter']['Value']

def handler(event, context):
    key = get_turnstile_key()  # Decrypt en 1a call
    # Warm starts usan cache
```

Con SnapStart, secret se cachea en snapshot (sin repeats).

## VPC (NO recomendado)

Lambda VPC:
- Cold start +1-2 seg (ENI attachment)
- NAT Gateway: $32/mes para acceso fuera VPC
- DynamoDB, SES, SSM: AWS-managed (no necesitan VPC)

**Conclusion**: NO VPC aqui.

## IAM Access Analyzer

Post-deploy, generar policy optima:

```bash
aws accessanalyzer validate-policy \
  --policy-document file://policy.json \
  --policy-type IDENTITY_POLICY

# Generar desde CloudTrail
aws accessanalyzer generate-finding-recommendations \
  --access-logs-bucket trail-bucket \
  --analysis-arn arn:aws:access-analyzer:region:account:analyzer/name
```

## Audit trail

Habilitar CloudTrail para auditar acceso a SSM:

```yaml
CloudTrail:
  Type: AWS::CloudTrail::Trail
  Properties:
    S3BucketName: !Ref TrailBucket
    IncludeGlobalServiceEvents: true
    EventSelectors:
      - ReadWriteType: All
        IncludeManagementEvents: true
        DataResources:
          - Type: AWS::SSM::Parameter
            Values:
              - arn:aws:ssm:*:*:parameter/portfolio/*
```

Todos los GetParameter calls de Lambda quedan registrados.

Verificado a fecha 2026-05-13.
