# Deployment con AWS SAM

> AWS Serverless Application Model: template.yaml, build, deploy, sam local,
> sam logs, samconfig.toml, troubleshooting.

[← Anterior: Cold start opt](./04-cold-start-optimization.md) | [Siguiente: IAM security →](./06-iam-security.md)

## Instalacion de SAM CLI

```bash
# macOS (via Homebrew)
brew tap aws/tap
brew install aws-sam-cli

# Linux (direct download)
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip -d sam-installation
./sam-installation/install

# Verify
sam --version  # SAM CLI, version X.Y.Z
```

## Estructura de proyecto

```
portfolio-lambdas/
├── template.yaml              # IaC: todos los recursos
├── samconfig.toml             # Config de deployment (interactivo)
├── events/                    # Test events para sam local invoke
│   ├── contact.json
│   ├── tracking-pixel.json
│   └── stream-processor.json
├── src/
│   ├── contact_form/
│   │   ├── handler.py         # Contact form handler
│   │   └── requirements.txt
│   ├── tracking_pixel/
│   │   ├── handler.py
│   │   └── requirements.txt
│   ├── stream_processor/
│   │   ├── handler.py
│   │   └── requirements.txt
│   ├── common/
│   │   └── turnstile.py       # Validacion Turnstile (compartida)
│   └── layers/
│       ├── python-deps/       # Shared dependencies (layer)
│       │   ├── requirements.txt
│       │   └── build.sh
│       └── utils/
│           ├── validators.py
│           └── secrets.py
└── tests/                     # Unit tests
    ├── conftest.py
    ├── test_contact_handler.py
    └── test_tracking_pixel.py
```

## template.yaml: IaC de todo el stack

Ejemplo completo con 3 Lambdas + API Gateway + DynamoDB + SES + KMS:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Description: Portfolio contact form, tracking pixel, stream processor

Globals:
  Function:
    Timeout: 30
    MemorySize: 512
    Runtime: python3.13
    Architectures:
      - x86_64
    EphemeralStorage:
      Size: 512
    Environment:
      Variables:
        POWERTOOLS_SERVICE_NAME: portfolio-lambdas
        POWERTOOLS_LOG_LEVEL: INFO
        AWS_NODEJS_CONNECTION_REUSE_ENABLED: '1'

Parameters:
  Stage:
    Type: String
    Default: dev
    AllowedValues: [dev, prod]
    Description: Deployment stage
  
  SenderEmail:
    Type: String
    Description: SES verified email for notifications
  
  TurnstileSecretSSMPath:
    Type: String
    Default: /portfolio/turnstile-secret
    Description: SSM Parameter path for Turnstile secret

Resources:
  # ==================== DYNAMODB TABLES ====================
  
  ContactsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${AWS::StackName}-contacts'
      BillingMode: PAY_PER_REQUEST  # On-demand (free tier)
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
        - AttributeName: createdAt
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH
        - AttributeName: createdAt
          KeyType: RANGE
      TimeToLiveSpecification:
        AttributeName: expirationTime
        Enabled: true
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: false
      Tags:
        - Key: Stage
          Value: !Ref Stage

  TrackingPixelTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${AWS::StackName}-tracking'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: sessionId
          AttributeType: S
        - AttributeName: timestamp
          AttributeType: S
      KeySchema:
        - AttributeName: sessionId
          KeyType: HASH
        - AttributeName: timestamp
          KeyType: RANGE
      TimeToLiveSpecification:
        AttributeName: ttl
        Enabled: true
      StreamSpecification:
        StreamViewType: NEW_IMAGE

  # ==================== LAYERS ====================
  
  PythonDepsLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: !Sub '${AWS::StackName}-python-deps'
      Description: Shared Python dependencies (boto3, powertools, pydantic)
      ContentUri: src/layers/python-deps/
      CompatibleRuntimes:
        - python3.13
    Metadata:
      BuildMethod: python3.13

  UtilsLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: !Sub '${AWS::StackName}-utils'
      Description: Portfolio utility modules
      ContentUri: src/layers/utils/
      CompatibleRuntimes:
        - python3.13

  # ==================== LAMBDA FUNCTIONS ====================
  
  ContactFormFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-contact-form'
      CodeUri: src/contact_form/
      Handler: handler.lambda_handler
      MemorySize: 512
      Timeout: 30
      Layers:
        - !Ref PythonDepsLayer
        - !Ref UtilsLayer
      Environment:
        Variables:
          CONTACTS_TABLE: !Ref ContactsTable
          SENDER_EMAIL: !Ref SenderEmail
          TURNSTILE_SECRET_PATH: !Ref TurnstileSecretSSMPath
          REGION: !Ref AWS::Region
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref ContactsTable
        - Statement:
            - Effect: Allow
              Action:
                - ses:SendEmail
              Resource: !Sub 'arn:aws:ses:${AWS::Region}:${AWS::AccountId}:identity/${SenderEmail}'
        - Statement:
            - Effect: Allow
              Action:
                - ssm:GetParameter
              Resource: !Sub 'arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter${TurnstileSecretSSMPath}'
        - Statement:
            - Effect: Allow
              Action:
                - kms:Decrypt
              Resource: !GetAtt KmsKey.Arn
      ReservedConcurrentExecutions: 10
      TracingConfig:
        Mode: Active
      Events:
        ContactFormApi:
          Type: Api
          Properties:
            Path: /contact
            Method: post
            RestApiId: !Ref PortfolioApi
            Auth:
              ApiKeyRequired: false

  TrackingPixelFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-tracking-pixel'
      CodeUri: src/tracking_pixel/
      Handler: handler.lambda_handler
      MemorySize: 256
      Timeout: 10
      Layers:
        - !Ref PythonDepsLayer
        - !Ref UtilsLayer
      Environment:
        Variables:
          TRACKING_TABLE: !Ref TrackingPixelTable
          TTL_SECONDS: '2592000'  # 30 dias
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref TrackingPixelTable
      TracingConfig:
        Mode: Active
      Events:
        TrackingPixelApi:
          Type: Api
          Properties:
            Path: /pixel
            Method: post
            RestApiId: !Ref PortfolioApi

  StreamProcessorFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-stream-processor'
      CodeUri: src/stream_processor/
      Handler: handler.lambda_handler
      MemorySize: 256
      Timeout: 30
      Layers:
        - !Ref PythonDepsLayer
        - !Ref UtilsLayer
      TracingConfig:
        Mode: Active
      Events:
        TrackingStream:
          Type: DynamoDB
          Properties:
            Stream: !GetAtt TrackingPixelTable.StreamArn
            StartingPosition: LATEST
            BatchSize: 100

  # ==================== API GATEWAY ====================
  
  PortfolioApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Stage
      TracingEnabled: true
      MethodSettings:
        - ResourcePath: '/*'
          HttpMethod: '*'
          LoggingLevel: INFO
          DataTraceEnabled: true
          MetricsEnabled: true
          ThrottleSettings:
            BurstLimit: 100
            RateLimit: 30  # 30 req/sec per IP
      Cors:
        AllowMethods: "'POST,OPTIONS'"
        AllowHeaders: "'Content-Type,X-Turnstile-Token'"
        AllowOrigin: "'https://the-full-stack.com'"
        MaxAge: 86400

  # ==================== KMS ENCRYPTION ====================
  
  KmsKey:
    Type: AWS::KMS::Key
    Properties:
      Description: Portfolio Lambda encryption key
      KeyPolicy:
        Version: '2012-10-17'
        Statement:
          - Sid: Enable IAM User Permissions
            Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
            Action: 'kms:*'
            Resource: '*'
          - Sid: Allow Lambda
            Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action:
              - 'kms:Decrypt'
            Resource: '*'

  KmsKeyAlias:
    Type: AWS::KMS::Alias
    Properties:
      AliasName: !Sub 'alias/${AWS::StackName}-key'
      TargetKeyId: !Ref KmsKey

Outputs:
  ContactFormApiEndpoint:
    Description: API Gateway endpoint for contact form
    Value: !Sub 'https://${PortfolioApi}.execute-api.${AWS::Region}.amazonaws.com/${Stage}/contact'
  
  TrackingPixelEndpoint:
    Description: API Gateway endpoint for tracking pixel
    Value: !Sub 'https://${PortfolioApi}.execute-api.${AWS::Region}.amazonaws.com/${Stage}/pixel'
  
  ContactsTableName:
    Description: DynamoDB table for contacts
    Value: !Ref ContactsTable
  
  TrackingTableName:
    Description: DynamoDB table for tracking
    Value: !Ref TrackingPixelTable
```

## Lifecycle: build, deploy, test

### 1. Validar template

```bash
sam validate --template template.yaml
# "template.yaml is valid"
```

### 2. Build (prepara codigo + dependencies)

```bash
# Sin Docker (asume que python3.13 esta en PATH)
sam build

# Con Docker (recomendado, evita problemas binarios)
sam build --use-container

# Output: .aws-sam/build/ con codigo transpilado
```

### 3. Deploy (interactivo)

Primer deploy:

```bash
sam deploy --guided

# Prompts:
# Stack name: portfolio-lambdas
# AWS Region: us-east-1
# Parameter SenderEmail: pablo@example.com
# Parameter TurnstileSecretSSMPath: /portfolio/turnstile-secret
# Confirm changes before deploy: Y
# SAM CLI now creates CloudFormation stack...
```

Genera `samconfig.toml`:

```toml
[default.deploy.parameters]
stack_name = "portfolio-lambdas"
s3_bucket = "aws-sam-cli-managed-default-samclisourcebucket-xxx"
s3_prefix = "portfolio-lambdas"
region = "us-east-1"
confirm_changeset = true
```

Deploy subsecuentes:

```bash
sam deploy  # Usa samconfig.toml
# o
sam deploy --stack-name portfolio-lambdas --region us-east-1
```

### 4. Invocar local (sin deployment)

Crear event test:

```bash
# events/contact.json
{
  "httpMethod": "POST",
  "path": "/contact",
  "body": "{\"name\":\"Pablo\",\"email\":\"pablo@example.com\",\"message\":\"Hola\",\"service\":\"web\"}",
  "headers": {
    "X-Turnstile-Token": "test-token-123"
  }
}
```

Invocar:

```bash
sam local invoke ContactFormFunction -e events/contact.json

# Output:
# ...
# StatusCode: 201
# {"contactId": "contact-abc123"}
```

### 5. Local API server

```bash
sam local start-api
# Listening on http://127.0.0.1:3000

# En otra terminal:
curl -X POST http://localhost:3000/contact \
  -H "Content-Type: application/json" \
  -d '{"name":"Pablo","email":"pablo@example.com",...}'
```

Requiere Docker corriendo.

### 6. Ver logs

```bash
# Tail de logs en tiempo real (post-deploy)
sam logs -n ContactFormFunction --tail

# Logs de stack
sam logs --stack-name portfolio-lambdas --tail

# Filtrar por tiempo
sam logs -n ContactFormFunction --start-time "5 min ago"
```

## samconfig.toml: versionable?

NO commitear `samconfig.toml` si contiene:
- Stack names privados
- S3 bucket names specificos
- AWS account ID

Crear `samconfig.toml.template` en repo (generico), developers hacen copy
local.

## Troubleshooting comun

| Error | Causa | Fix |
|-------|-------|-----|
| `Template validation failed` | YAML syntax invalid | `sam validate --template template.yaml` + revisar indentacion |
| `No changes are to be performed` | Template no cambio desde ultimo deploy | Normal, no hacer nada |
| `Unresolved resource` | Reference a recurso no definido | Chequear `!Ref` names |
| `AccessDenied` en deploy | IAM user sin permisos | Verificar credenciales AWS (`aws sts get-caller-identity`) |
| `Function timeout during build` | Layer o deps muy grandes | `sam build --use-container` |
| `Cannot access table in local invoke` | DynamoDB no existe local | Usar `sam local start-dynamodb` en paralelo (no recomendado, usar mocks) |

Verificado a fecha 2026-05-13.
