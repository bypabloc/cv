# Deployment con AWS SAM (Infrastructure as Code)

> Template SAM completo para desplegar 2 tablas + 2 Lambda functions + IAM roles.

## Template SAM (template.yaml)

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2013-12-31

Description: |
  Portfolio DynamoDB infrastructure:
  - Tabla contacts: formulario de contacto
  - Tabla tracking: page views con TTL 60 dias
  - Lambda handlers: contact-form, tracking-pixel

Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, prod]
  
  TablePrefix:
    Type: String
    Default: portfolio
    Description: Prefijo para nombre de tablas

Globals:
  Function:
    Runtime: python3.13
    Timeout: 30
    MemorySize: 256
    Environment:
      Variables:
        CONTACTS_TABLE: !Ref ContactsTable
        TRACKING_TABLE: !Ref TrackingTable

Resources:
  # ===== DYNAMODB TABLES =====
  
  ContactsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${TablePrefix}-${Environment}-contacts'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: Purpose
          Value: ContactForm

  TrackingTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${TablePrefix}-${Environment}-tracking'
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
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: Purpose
          Value: PageViewTracking

  # ===== LAMBDA FUNCTIONS =====
  
  ContactFormFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub '${TablePrefix}-${Environment}-contact-form'
      CodeUri: src/handlers/contact_form/
      Handler: app.lambda_handler
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref ContactsTable
      Environment:
        Variables:
          CONTACTS_TABLE: !Ref ContactsTable
      Events:
        ApiEvent:
          Type: Api
          Properties:
            RestApiId: !Ref PortfolioApi
            Path: /contact
            Method: POST
            # CORS: 
            #   AllowMethods: POST
            #   AllowHeaders: '*'
            #   AllowOrigin: '*'

  TrackingPixelFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub '${TablePrefix}-${Environment}-tracking-pixel'
      CodeUri: src/handlers/tracking_pixel/
      Handler: app.lambda_handler
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref TrackingTable
      Environment:
        Variables:
          TRACKING_TABLE: !Ref TrackingTable

  # ===== API GATEWAY =====
  
  PortfolioApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Environment
      TracingEnabled: true
      MethodSettings:
        - ResourcePath: '/*'
          HttpMethod: '*'
          LoggingLevel: INFO
          DataTraceEnabled: true
          MetricsEnabled: true

Outputs:
  ContactsTableName:
    Description: Nombre de tabla Contacts
    Value: !Ref ContactsTable
    Export:
      Name: !Sub '${AWS::StackName}-ContactsTable'

  TrackingTableName:
    Description: Nombre de tabla Tracking
    Value: !Ref TrackingTable
    Export:
      Name: !Sub '${AWS::StackName}-TrackingTable'

  ContactFormApiEndpoint:
    Description: API endpoint para contactos
    Value: !Sub 'https://${PortfolioApi}.execute-api.${AWS::Region}.amazonaws.com/${Environment}/contact'
    Export:
      Name: !Sub '${AWS::StackName}-ContactFormEndpoint'

  ContactFormFunctionArn:
    Description: ARN de Lambda contact-form
    Value: !GetAtt ContactFormFunction.Arn
    Export:
      Name: !Sub '${AWS::StackName}-ContactFormFunctionArn'

  TrackingPixelFunctionArn:
    Description: ARN de Lambda tracking-pixel
    Value: !GetAtt TrackingPixelFunction.Arn
    Export:
      Name: !Sub '${AWS::StackName}-TrackingPixelFunctionArn'
```

## Estructura de Directorio

```
.
├── src/
│   └── handlers/
│       ├── contact_form/
│       │   ├── app.py          # Lambda handler contactos
│       │   └── requirements.txt
│       └── tracking_pixel/
│           ├── app.py          # Lambda handler tracking
│           └── requirements.txt
├── template.yaml               # SAM template
├── samconfig.toml              # Configuracion SAM
└── README.md
```

## Archivos Handler

**src/handlers/contact_form/app.py:**
```python
import json
import boto3
import uuid
import time
from decimal import Decimal
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
contacts_table = dynamodb.Table(os.environ['CONTACTS_TABLE'])

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        
        item = {
            'id': str(uuid.uuid4()),
            'email': body['email'],
            'name': body['name'],
            'message': body['message'],
            'service_type': body.get('service_type', 'generic'),
            'company': body.get('company'),
            'budget': Decimal(str(body.get('budget', 0))),
            'timeline': body.get('timeline'),
            'created_at': int(time.time()),
        }
        
        contacts_table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'id': item['id']}),
        }
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Missing field: {e}'}),
        }
```

**src/handlers/tracking_pixel/app.py:**
```python
import json
import boto3
import uuid
import time
import os

dynamodb = boto3.resource('dynamodb')
tracking_table = dynamodb.Table(os.environ['TRACKING_TABLE'])

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        now = int(time.time())
        
        item = {
            'session_id': body['session_id'],
            'page_id': str(uuid.uuid4()),
            'url': body['url'],
            'referrer': body.get('referrer'),
            'created_at': now,
            'expires_at': now + (60 * 24 * 60 * 60),  # TTL 60 dias
        }
        
        tracking_table.put_item(Item=item)
        
        return {'statusCode': 204}
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)}),
        }
```

## Deployment

```bash
# Build
sam build

# Deploy (GUI)
sam deploy --guided
# Responder:
#   Stack name: portfolio-dynamodb
#   Region: us-west-2
#   Environment: dev
#   Confirmar cambios

# Deploy (CLI, conocidos)
sam deploy --stack-name portfolio-dynamodb --region us-west-2 --parameter-overrides Environment=prod

# Ver outputs
aws cloudformation describe-stacks \
  --stack-name portfolio-dynamodb \
  --region us-west-2 \
  --query 'Stacks[0].Outputs'
```

## Verificacion Post-Deploy

```bash
# Listar tablas
aws dynamodb list-tables --region us-west-2

# Describir tabla contacts
aws dynamodb describe-table \
  --table-name portfolio-dev-contacts \
  --region us-west-2

# Test API (si creaste Gateway)
curl -X POST https://xxx.execute-api.us-west-2.amazonaws.com/dev/contact \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test","message":"Hello"}'
```

## samconfig.toml (Opcional)

```toml
version = 0.1

[default]
[default.build]
watch_exclude = [".git", "*.pyc"]

[default.deploy]
region = "us-west-2"
confirm_changeset = true
capabilities = "CAPABILITY_IAM"
parameter_overrides = [
  "Environment=dev"
]
```

## Paso Siguiente

- Costos: [08-cost-optimization.md](08-cost-optimization.md)
- Seguridad: [09-security-best-practices.md](09-security-best-practices.md)
