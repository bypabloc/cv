# Deployment con SAM template

> Template SAM completo con API Gateway + WAF + Lambdas + custom domain.
> Comandos: sam build, sam deploy, verificacion, troubleshoot.

[← Request validation](./06-request-validation.md) | [README](./README.md) | [Siguiente: Monitoring →](./08-monitoring-logs.md)

## Estructura de archivos SAM

```
portfolio/
├── .aws/
│   ├── template.yaml          # SAM template principal
│   ├── samconfig.toml         # Configuracion de deploy
│   └── parameters/
│       ├── prod.json          # Parametros para prod
│       └── dev.json           # Parametros para dev
├── functions/
│   ├── contact/
│   │   ├── handler.py         # Lambda handler
│   │   └── requirements.txt
│   └── track/
│       ├── handler.py
│       └── requirements.txt
└── tests/
    ├── unit/
    │   └── test_handlers.py
    └── integration/
        └── test_api.py
```

## Template SAM (template.yaml)

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: 'Portfolio API: contact form, tracking pixel'

Parameters:
  Environment:
    Type: String
    Default: prod
    AllowedValues: [dev, prod]
  
  ApiDomainName:
    Type: String
    Default: api.the-full-stack.com
    Description: Custom domain for API Gateway
  
  CertificateArn:
    Type: String
    Description: ACM certificate ARN in us-east-1
  
  AlertEmail:
    Type: String
    Default: pablo@the-full-stack.com
    Description: Email for CloudWatch alarms

Globals:
  Function:
    Runtime: python3.13
    Handler: handler.lambda_handler
    Timeout: 30
    MemorySize: 256
    Tracing: Active
    Environment:
      Variables:
        ENVIRONMENT: !Ref Environment
        POWERTOOLS_SERVICE_NAME: portfolio-api
        POWERTOOLS_LOG_LEVEL: INFO

Resources:
  # ===== API Gateway REST API =====
  PortfolioApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Environment
      Name: portfolio-api
      Description: Portfolio contact and tracking APIs
      TracingEnabled: true
      EndpointConfiguration:
        Type: REGIONAL
      
      # CORS configuration (uno solo, agregar otros manualmente)
      Cors:
        AllowMethods: "'POST,OPTIONS'"
        AllowHeaders: "'Content-Type'"
        AllowOrigin: "'https://the-full-stack.com'"
        MaxAge: "'600'"
      
      # Request validation
      Models:
        ContactRequest:
          type: object
          required: [email, message]
          properties:
            email:
              type: string
              format: email
              minLength: 5
              maxLength: 254
            message:
              type: string
              minLength: 10
              maxLength: 1000
            name:
              type: string
              minLength: 1
              maxLength: 100
          additionalProperties: false
        
        TrackRequest:
          type: object
          required: [page_url, visitor_id]
          properties:
            page_url:
              type: string
              format: uri
            visitor_id:
              type: string
              pattern: '^[a-f0-9\-]{36}$'
            referrer:
              type: string
      
      # Method settings: throttling + validation
      MethodSettings:
        - ResourcePath: /contact
          HttpMethod: POST
          ThrottleSettings:
            RateLimit: 3
            BurstLimit: 5
          LoggingLevel: INFO
          DataTraceEnabled: true
        
        - ResourcePath: /track
          HttpMethod: POST
          ThrottleSettings:
            RateLimit: 30
            BurstLimit: 60
          LoggingLevel: INFO
      
      # Custom domain
      Domain:
        DomainName: !Ref ApiDomainName
        CertificateArn: !Ref CertificateArn
        BasePath:
          - /
      
      # Access logging
      AccessLogSetting:
        DestinationArn: !GetAtt ApiAccessLogGroup.Arn
        Format: >
          {
            "requestId":"$context.requestId",
            "ip":"$context.identity.sourceIp",
            "requestTime":"$context.requestTime",
            "httpMethod":"$context.httpMethod",
            "resourcePath":"$context.resourcePath",
            "status":"$context.status",
            "protocol":"$context.protocol",
            "responseLength":"$context.responseLength",
            "integrationLatency":"$context.integration.latency",
            "userAgent":"$context.identity.userAgent"
          }

  # ===== CloudWatch Log Group para API =====
  ApiAccessLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub /aws/apigateway/portfolio/${Environment}
      RetentionInDays: 30

  # ===== WAF Web ACL =====
  PortfolioWebAcl:
    Type: AWS::WAFv2::WebACL
    Properties:
      Name: portfolio-waf
      Scope: REGIONAL
      DefaultAction:
        Allow: {}
      Rules:
        - Name: RateLimitContact
          Priority: 0
          Statement:
            RateBasedStatement:
              Limit: 3
              AggregateKeyType: IP
              ScopeDownStatement:
                ByteMatchStatement:
                  SearchString: /contact
                  FieldToMatch:
                    UriPath: {}
                  TextTransformation: [NONE]
                  PositionalConstraint: CONTAINS
          Action:
            Block:
              CustomResponse:
                ResponseCode: 429
                CustomResponseBodyKey: RateLimitMsg
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: ContactRateLimit
        
        - Name: RateLimitTrack
          Priority: 1
          Statement:
            RateBasedStatement:
              Limit: 30
              AggregateKeyType: IP
              ScopeDownStatement:
                ByteMatchStatement:
                  SearchString: /track
                  FieldToMatch:
                    UriPath: {}
                  TextTransformation: [NONE]
                  PositionalConstraint: CONTAINS
          Action:
            Block:
              CustomResponse:
                ResponseCode: 429
                CustomResponseBodyKey: RateLimitMsg
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: TrackRateLimit
      
      CustomResponseBodies:
        RateLimitMsg:
          Content: '{"error":"Rate limit exceeded","code":"RATE_LIMIT"}'
          ContentType: APPLICATION_JSON
      
      VisibilityConfig:
        SampledRequestsEnabled: true
        CloudWatchMetricsEnabled: true
        MetricName: PortfolioWaf

  # Asociar WAF a API Gateway stage
  WafAssociation:
    Type: AWS::WAFv2::WebACLAssociation
    Properties:
      ResourceArn: !Sub arn:aws:apigateway:${AWS::Region}::/restapis/${PortfolioApi}/stages/${Environment}
      WebACLArn: !GetAtt PortfolioWebAcl.Arn

  # ===== Lambda Functions =====
  ContactFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub portfolio-contact-${Environment}
      CodeUri: functions/contact/
      Description: Procesa formulario de contacto
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref ContactTable
        - CloudWatchPutMetricPolicy: {}
        - AWSXRayDaemonWriteAccess
      Environment:
        Variables:
          CONTACTS_TABLE: !Ref ContactTable
      Events:
        ApiEvent:
          Type: Api
          Properties:
            RestApiId: !Ref PortfolioApi
            Path: /contact
            Method: POST

  TrackFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub portfolio-track-${Environment}
      CodeUri: functions/track/
      Description: Tracking pixel para analytics
      Policies:
        - CloudWatchPutMetricPolicy: {}
        - AWSXRayDaemonWriteAccess
      Events:
        ApiEvent:
          Type: Api
          Properties:
            RestApiId: !Ref PortfolioApi
            Path: /track
            Method: POST

  # ===== DynamoDB para contacts =====
  ContactTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub portfolio-contacts-${Environment}
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
        - AttributeName: timestamp
          AttributeType: N
      KeySchema:
        - AttributeName: id
          KeyType: HASH
        - AttributeName: timestamp
          KeyType: RANGE
      TTL:
        AttributeName: ttl
        Enabled: true

  # ===== CloudWatch Alarms =====
  ThrottledRequestsAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub portfolio-api-throttled-${Environment}
      AlarmDescription: Alert if API is being throttled
      MetricName: ThrottledRequests
      Namespace: AWS/ApiGateway
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 1
      Threshold: 5
      ComparisonOperator: GreaterThanThreshold
      AlarmActions:
        - !Ref AlertTopic

  4xxErrorsAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub portfolio-api-4xx-${Environment}
      MetricName: 4XXError
      Namespace: AWS/ApiGateway
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 1
      Threshold: 50
      ComparisonOperator: GreaterThanThreshold
      AlarmActions:
        - !Ref AlertTopic

  # ===== SNS Topic para alertas =====
  AlertTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub portfolio-api-alerts-${Environment}
      DisplayName: Portfolio API Alerts
      Subscription:
        - Endpoint: !Ref AlertEmail
          Protocol: email

Outputs:
  ApiEndpoint:
    Description: API Gateway endpoint URL
    Value: !Sub https://${ApiDomainName}
    Export:
      Name: !Sub ${AWS::StackName}-ApiEndpoint
  
  ApiId:
    Description: REST API ID
    Value: !Ref PortfolioApi
    Export:
      Name: !Sub ${AWS::StackName}-ApiId
  
  WebAclArn:
    Description: WAF Web ACL ARN
    Value: !GetAtt PortfolioWebAcl.Arn
  
  ContactsTableName:
    Description: DynamoDB table for contacts
    Value: !Ref ContactTable
```

## samconfig.toml

```toml
version = 0.1

[default]
[default.deploy]
region = "us-east-1"
stack_name = "portfolio-api-stack"
s3_prefix = "portfolio-api"
confirm_changeset = false
capabilities = "CAPABILITY_IAM"
image_repositories = []
disable_rollback = true

[default.build]
cached = true
parallel = true

[prod]
[prod.deploy]
region = "us-east-1"
stack_name = "portfolio-api-prod"
s3_bucket = "portfolio-sam-artifacts-prod"
s3_prefix = "portfolio-api"
parameter_overrides = [
  "Environment=prod",
  "ApiDomainName=api.the-full-stack.com",
  "CertificateArn=arn:aws:acm:us-east-1:ACCOUNT:certificate/abc123",
  "AlertEmail=pablo@the-full-stack.com"
]
```

## Comandos: build, deploy, verificar

```bash
# 1. Build (compila Lambda, valida template)
sam build

# 2. Deploy (primera vez o update)
sam deploy --guided  # Preguntas interactivas
# O si ya tienes samconfig.toml:
sam deploy --config-env prod

# 3. Verificar stack en CloudFormation
aws cloudformation describe-stacks \
  --stack-name portfolio-api-prod \
  --region us-east-1 \
  --query 'Stacks[0].[StackStatus,CreationTime]'

# 4. Ver outputs
aws cloudformation describe-stacks \
  --stack-name portfolio-api-prod \
  --region us-east-1 \
  --query 'Stacks[0].Outputs'

# 5. Test endpoint
curl -X POST https://api.the-full-stack.com/contact \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","message":"Hello world"}'

# 6. Ver logs
sam logs -n ContactFunction --stack-name portfolio-api-prod --tail

# 7. Borrar stack (cleanup)
aws cloudformation delete-stack \
  --stack-name portfolio-api-prod \
  --region us-east-1
```

## Troubleshooting

### Error: ACM certificate not found

```
Parameter validation failed: Invalid ARN: arn:aws:acm:...
```

Causa: certificate no existe o esta en region diferente.
Solucion: crear cert en us-east-1:

```bash
aws acm request-certificate \
  --domain-name api.the-full-stack.com \
  --validation-method DNS \
  --region us-east-1
```

### Error: Stack already exists

```
AlreadyExistsException
```

Solucion: usar `--no-fail-on-empty-changeset` o borrar stack viejo.

### Lambdas no invocadas (403 Forbidden)

Causa: WAF o API Gateway rechaza por validacion.
Solucion: verificar WAF rules y logs en CloudWatch.

## Local testing con SAM

```bash
# Levantar API local
sam local start-api --port 3001

# Test con curl
curl -X POST http://localhost:3001/contact \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","message":"Test local"}'

# Ver logs en tiempo real
# (SAM imprime logs del Lambda local en stdout)
```

Verificado a fecha 2026-05-13.
