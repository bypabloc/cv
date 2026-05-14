# Handler patterns y types de events

> Estructura del handler Lambda: signatures, event types (API Gateway REST
> vs HTTP), response shapes, error handling.

[← Anterior: Architecture](./01-architecture.md) | [Siguiente: Powertools →](./03-powertools.md)

## Handler signature basica

Todo Lambda handler Python tiene esta firma:

```python
def handler(event, context):
    # event: dict con datos del invocador (API Gateway, S3, etc.)
    # context: LambdaContext con metadatos de invocacion
    return response  # dict serializable a JSON, o raise Exception
```

### Event (dict)

Depende del source del evento:
- API Gateway REST: `event['httpMethod']`, `event['body']`, etc.
- API Gateway HTTP: similar pero formato simplificado (v2.0)
- S3: `event['Records'][0]['s3']['bucket']['name']`
- DynamoDB Streams: `event['Records']` con `dynamodb` data
- Custom CloudWatch Events: estructura personalizada

Para contact-form y tracking-pixel, el source es **API Gateway REST**.

### Context (LambdaContext)

Metadata de invocacion disponible:

```python
context.function_name      # "contact-form"
context.function_version   # "$LATEST" o version number
context.invoked_function_arn
context.memory_limit_in_mb # 512
context.aws_request_id     # correlation ID, unico por invocacion
context.log_group_name     # "/aws/lambda/contact-form"
context.log_stream_name    # timestamp + random suffix
context.identity           # ClientContext si viene de mobile SDK
context.client_context

# Importante para X-Ray:
context.x_amzn_trace_id   # correlation ID X-Ray
```

Usar `context.aws_request_id` en logs para correlacionar con X-Ray.

## API Gateway REST (v1.0 event)

Event shape:

```python
{
    "httpMethod": "POST",
    "path": "/contact",
    "headers": {
        "Content-Type": "application/json",
        "User-Agent": "...",
        "X-Forwarded-For": "..."
    },
    "queryStringParameters": {
        "foo": "bar"  # ?foo=bar
    },
    "body": '{"name":"Pablo","email":"user@example.com"}',  # string
    "isBase64Encoded": False,
    "requestContext": {
        "accountId": "123456789",
        "apiId": "xyz123",
        "stage": "prod",
        "requestId": "...",
        "sourceIp": "192.168.1.1"
    }
}
```

Response shape esperada (v1.0):

```python
{
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json",
        "X-Custom-Header": "value"
    },
    "body": '{"status":"ok","contactId":"xyz123"}',  # string JSON
    "isBase64Encoded": False  # si el body es binario base64
}
```

Handler pattern:

```python
import json

def contact_handler(event, context):
    try:
        # Parse body
        body = json.loads(event.get('body', '{}'))
        
        # Validate input
        if not all(k in body for k in ['name', 'email', 'message']):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'missing required fields'})
            }
        
        # Process
        contact_id = save_to_dynamodb(body)
        send_email(body)
        
        # Return success
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'contactId': contact_id})
        }
    
    except Exception as e:
        # Log error con correlation ID
        print(f'RequestID: {context.aws_request_id} | Error: {e}')
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'internal server error'})
        }
```

## API Gateway HTTP (v2.0 event)

Formato simplificado, soporte para cookies nativo:

```python
{
    "version": "2.0",
    "routeKey": "POST /contact",
    "rawPath": "/contact",
    "headers": {
        "content-type": "application/json",
        "x-forwarded-for": "..."
    },
    "queryStringParameters": "foo=bar&baz=qux",  # string, no dict
    "body": '{"name":"..."}',
    "requestContext": {
        "http": {
            "method": "POST",
            "path": "/contact",
            "sourceIp": "192.168.1.1"
        },
        "requestId": "...",
        "stage": "$default"
    }
}
```

Response (v2.0 permite API Gateway inferred response):

```python
# Opcion 1: formato explicit (compatible con v1.0)
return {
    "statusCode": 201,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps({"contactId": "xyz"})
}

# Opcion 2: inferred response (v2.0 only)
# API Gateway asume statusCode=200 si no lo especificas
return {"contactId": "xyz"}  # auto-serializa a JSON
```

Para este proyecto, usar **v1.0 (REST API)** porque es explicitamente
compatible con la mayoria de SAM templates y mas predecible.

## Error handling

Lambda distingue entre:
- **Errores de handler**: uncaught exception en el codigo
- **Lambda errors**: timeout, memory exceeded, permissions denied

Si tu handler lanza una exception (no catcheada), Lambda devuelve:

```json
{
  "statusCode": 500,
  "body": "Internal server error"
}
```

**Best practice**: catch en el handler, return 4xx/5xx HTTP response explicito.

```python
def contact_handler(event, context):
    try:
        # ... code ...
    except ValueError as e:
        # Validacion de input
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        # Unexpected error
        logger.exception(f'Unhandled error: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'internal server error'})
        }
```

## Base64 encoding

Si necesitas retornar binario (PDF, imagen), marcar `isBase64Encoded: True`:

```python
import base64

def get_pdf_handler(event, context):
    pdf_bytes = generate_pdf()  # bytes
    encoded = base64.b64encode(pdf_bytes).decode('utf-8')
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/pdf'},
        'body': encoded,
        'isBase64Encoded': True
    }
```

Para contact-form y tracking-pixel, **no aplica** (JSON responses).

## Decorator patterns con Powertools

AWS Lambda Powertools v3 simplifica handlers:

```python
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.data_classes.api_gateway_event import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.data_classes.lambda_context import LambdaContext

logger = Logger()
tracer = Tracer()
metrics = Metrics()

@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_cold_start_metric
def contact_handler(event: APIGatewayProxyEvent, context: LambdaContext) -> dict:
    """
    Procesa form de contacto validado.
    
    Logs automaticos (correlation ID, cold start).
    Trazas a X-Ray (segments).
    Metricas a CloudWatch (invocaciones, duracion).
    """
    # Acceso tipado a event properties
    body = event.json_body  # auto-parsea JSON
    
    # ... procesamiento ...
    
    return {
        'statusCode': 201,
        'body': json.dumps({'contactId': 'xyz'})
    }
```

Ver [03-powertools.md](./03-powertools.md) para detalles.

Verificado a fecha 2026-05-13.
