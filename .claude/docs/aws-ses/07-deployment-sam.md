# Deployment con SAM: infrastructure-as-code para SES + Lambda

> AWS Serverless Application Model template para desplegar
> Lambda + SES + IAM + SNS notifications.

## SAM template basico

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Description: Contact notification Lambda with SES

Parameters:
  EnvironmentName:
    Type: String
    Default: dev
    AllowedValues: [dev, prod]
    Description: Deployment environment

Globals:
  Function:
    Timeout: 30
    Memory: 256
    Runtime: python3.13
    Environment:
      Variables:
        ENVIRONMENT: !Ref EnvironmentName
        SES_REGION: us-west-2
        SES_FROM: no-reply@the-full-stack.com
        OWNER_EMAIL: pacg1991@gmail.com

Resources:
  # SNS Topic para bounce/complaint notifications
  SESNotificationTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub 'ses-bounces-complaints-${EnvironmentName}'
      DisplayName: 'SES Bounce and Complaint Notifications'

  # Lambda function para enviar emails
  ContactNotificationFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub 'portfolio-contact-${EnvironmentName}'
      CodeUri: src/
      Handler: contact_handler.lambda_handler
      Description: Send contact notification email via SES
      Policies:
        - Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - ses:SendEmail
                - ses:SendRawEmail
              Resource: '*'
              Condition:
                StringEquals:
                  'ses:FromAddress': !Sub '${SES_FROM}'
      Events:
        ContactAPI:
          Type: Api
          Properties:
            RestApiId: !Ref ContactAPIGateway
            Path: /contact
            Method: POST

  # API Gateway para el form de contacto
  ContactAPIGateway:
    Type: AWS::Serverless::Api
    Properties:
      Name: !Sub 'portfolio-contact-api-${EnvironmentName}'
      StageName: !Ref EnvironmentName
      TracingEnabled: true
      MethodSettings:
        - ResourcePath: '/*'
          HttpMethod: '*'
          LoggingLevel: INFO
          DataTraceEnabled: true

  # Lambda function para manejar bounce/complaint notifications
  BounceComplaintHandlerFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub 'ses-bounce-complaint-handler-${EnvironmentName}'
      CodeUri: src/
      Handler: bounce_complaint_handler.lambda_handler
      Runtime: python3.13
      Description: Handle SES bounce and complaint notifications
      Environment:
        Variables:
          DYNAMODB_TABLE: !Ref SuppressionListTable
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref SuppressionListTable
      Events:
        SNSEvent:
          Type: SNS
          Properties:
            Topic: !Ref SESNotificationTopic

  # SES Configuration Set para event tracking
  PortfolioConfigurationSet:
    Type: AWS::SES::ConfigurationSet
    Properties:
      Name: !Sub 'portfolio-${EnvironmentName}'

  # SES Configuration Set Event Destination (bounce/complaint)
  BounceComplaintEventDestination:
    Type: AWS::SES::ConfigurationSetEventDestination
    Properties:
      ConfigurationSetName: !Ref PortfolioConfigurationSet
      EventDestination:
        Name: BounceComplaintDestination
        Enabled: true
        MatchingEventTypes:
          - bounce
          - complaint
          - delivery
        SNSDestination:
          TopicARN: !GetAtt SESNotificationTopic.TopicArn

  # DynamoDB table para suppression list
  SuppressionListTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub 'email-suppression-${EnvironmentName}'
      AttributeDefinitions:
        - AttributeName: email
          AttributeType: S
        - AttributeName: timestamp
          AttributeType: N
      KeySchema:
        - AttributeName: email
          KeyType: HASH
        - AttributeName: timestamp
          KeyType: RANGE
      BillingMode: PAY_PER_REQUEST
      TTL:
        Enabled: true
        AttributeName: expiration_time
      StreamSpecification:
        StreamViewType: NEW_AND_OLD_IMAGES

Outputs:
  ContactAPIEndpoint:
    Description: Contact API endpoint
    Value: !Sub 'https://${ContactAPIGateway}.execute-api.${AWS::Region}.amazonaws.com/${EnvironmentName}/contact'
    Export:
      Name: !Sub '${AWS::StackName}-APIEndpoint'

  SNSTopicArn:
    Description: SNS Topic for SES notifications
    Value: !GetAtt SESNotificationTopic.TopicArn
    Export:
      Name: !Sub '${AWS::StackName}-SNSTopicArn'

  DynamoDBTableName:
    Description: DynamoDB suppression list table
    Value: !Ref SuppressionListTable
    Export:
      Name: !Sub '${AWS::StackName}-DynamoDBTable'
```

## Lambda handler: contact_handler.py

```python
import json
import os
import boto3
from botocore.exceptions import ClientError

ses = boto3.client('ses', region_name=os.getenv('SES_REGION', 'us-west-2'))

SES_FROM = os.getenv('SES_FROM', 'no-reply@the-full-stack.com')
OWNER_EMAIL = os.getenv('OWNER_EMAIL', 'pacg1991@gmail.com')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')

def lambda_handler(event, context):
    """
    API Gateway handler para contacto form.
    POST /contact con body JSON:
    {
        "name": "Pablo",
        "email": "user@example.com",
        "message": "Mensaje del usuario",
        "subdomain": "generic"
    }
    """
    try:
        # Parse body
        body = json.loads(event.get('body', '{}'))
        name = body.get('name', '').strip()
        email = body.get('email', '').strip()
        message = body.get('message', '').strip()
        subdomain = body.get('subdomain', 'generic').strip()

        # Validar inputs
        if not all([name, email, message]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required fields: name, email, message'
                }),
            }

        # Construir HTML del email
        html_body = build_html_email(name, email, message, subdomain)

        # Enviar via SES
        response = ses.send_email(
            Source=SES_FROM,
            Destination={'ToAddresses': [OWNER_EMAIL]},
            Message={
                'Subject': {
                    'Data': f'[{subdomain}] Nuevo contacto: {name}',
                    'Charset': 'UTF-8',
                },
                'Body': {
                    'Html': {'Data': html_body, 'Charset': 'UTF-8'},
                    'Text': {
                        'Data': f'Nombre: {name}\nEmail: {email}\nSubdomain: {subdomain}\n\nMensaje:\n{message}',
                        'Charset': 'UTF-8',
                    },
                },
            },
        )

        print(f'Email sent successfully. MessageId: {response["MessageId"]}')

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': True,
                'message': 'Thank you for contacting us!',
                'messageId': response['MessageId'],
            }),
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f'SES Error ({error_code}): {error_msg}')

        if error_code == 'MessageRejected':
            return api_error(400, 'Invalid email address or recipient not verified')
        elif error_code == 'MailFromDomainNotVerified':
            return api_error(500, 'Email service not properly configured')
        elif error_code == 'AccountSendingPausedException':
            return api_error(503, 'Email service temporarily unavailable')
        else:
            return api_error(500, 'Failed to send email')

    except Exception as e:
        print(f'Unexpected error: {str(e)}')
        return api_error(500, 'Internal server error')


def build_html_email(name: str, email: str, message: str, subdomain: str) -> str:
    """Construye HTML del email de notificacion."""
    return f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Nuevo contacto</title>
    </head>
    <body style="font-family: -apple-system, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background-color: #f9f9f9;">
        <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
                <td align="center" style="padding: 20px;">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <tr>
                            <td style="padding: 30px; border-bottom: 1px solid #eee;">
                                <h2 style="margin: 0 0 10px 0; color: #333;">Nuevo contacto</h2>
                                <p style="margin: 0; color: #666; font-size: 14px;">via {html_escape(subdomain)}</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 30px;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                                            <p style="margin: 0; font-size: 13px; color: #666;"><strong>Nombre:</strong></p>
                                            <p style="margin: 5px 0 0 0; font-size: 14px; color: #333;">{html_escape(name)}</p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                                            <p style="margin: 0; font-size: 13px; color: #666;"><strong>Email:</strong></p>
                                            <p style="margin: 5px 0 0 0; font-size: 14px;"><a href="mailto:{email}" style="color: #0066cc; text-decoration: none;">{html_escape(email)}</a></p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0;">
                                            <p style="margin: 0; font-size: 13px; color: #666;"><strong>Mensaje:</strong></p>
                                            <p style="margin: 5px 0 0 0; font-size: 14px; color: #333; line-height: 1.6;">{html_escape(message).replace(chr(10), '<br>')}</p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 20px; text-align: center; border-top: 1px solid #eee; color: #999; font-size: 12px;">
                                <p style="margin: 0;">Portfolio: https://the-full-stack.com</p>
                                <p style="margin: 5px 0 0 0;">Env: {ENVIRONMENT}</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    '''


def html_escape(text: str) -> str:
    """Escapa HTML para prevenir XSS."""
    return (
        text.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )


def api_error(status_code: int, message: str) -> dict:
    """Retorna respuesta de error API."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({'error': message}),
    }
```

## Deployment commands

```bash
# 1. Build SAM template
sam build

# 2. Guided deploy (primera vez)
sam deploy --guided
# Parametros:
# - Stack name: portfolio-contact-dev
# - Region: us-west-2
# - Parameter EnvironmentName: dev
# - Capabilities: CAPABILITY_IAM

# 3. Deploy sin confirmar (siguientes veces)
sam deploy --no-confirm-changeset

# 4. Ver outputs
aws cloudformation describe-stacks \
  --stack-name portfolio-contact-dev \
  --region us-west-2 \
  --query 'Stacks[0].Outputs'

# 5. Test local
sam local start-api

# 6. Cleanup (borrar stack)
aws cloudformation delete-stack --stack-name portfolio-contact-dev --region us-west-2
```

## Estructura del proyecto

```
.
├── template.yaml              # SAM template
├── src/
│   ├── contact_handler.py     # Lambda handler para envio
│   ├── bounce_complaint_handler.py  # Lambda para SNS
│   └── requirements.txt        # boto3, etc.
├── tests/
│   ├── unit/
│   │   └── test_contact_handler.py
│   └── integration/
│       └── test_contact_api.py
└── samconfig.toml             # SAM config (guardado post-deploy)
```

## Testing local

```bash
# Invocar Lambda local
sam local invoke ContactNotificationFunction -e events/contact.json

# Archivo: events/contact.json
{
  "body": "{\"name\": \"Test User\", \"email\": \"test@example.com\", \"message\": \"Test message\", \"subdomain\": \"generic\"}"
}

# Resultado esperado: HTTP 200 con messageId
```

## IAM Permissions (minimas)

El template ya incluye:

```yaml
Policies:
  - Version: '2012-10-17'
    Statement:
      - Effect: Allow
        Action:
          - ses:SendEmail
          - ses:SendRawEmail
        Resource: '*'
        Condition:
          StringEquals:
            'ses:FromAddress': no-reply@the-full-stack.com
```

**Nunca agregar**: `ses:*`, `ses:GetAccount`, `ses:ListVerifiedEmailAddresses`.
Solo lo minimo necesario.

## Monitoring post-deploy

```bash
# Ver logs de Lambda
sam logs -n ContactNotificationFunction --stack-name portfolio-contact-dev

# Ver CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=portfolio-contact-dev \
  --statistics Sum \
  --start-time 2026-05-13T00:00:00Z \
  --end-time 2026-05-14T00:00:00Z \
  --region us-west-2
```

## Fuentes

- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS SAM template specification](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-function.html)
- [SAM CLI commands](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference.html)

**Verificado 2026-05-13**
