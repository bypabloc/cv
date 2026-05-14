# AWS Lambda Powertools v3

> Toolkit oficial de AWS para structured logging, X-Ray tracing, CloudWatch
> metrics, event validation con Pydantic v2, decorators, idempotency.

[← Anterior: Handler patterns](./02-handler-patterns.md) | [Siguiente: Cold start opt →](./04-cold-start-optimization.md)

## Instalacion

```bash
# Solo logging + tracing
pip install aws-lambda-powertools

# Con Pydantic validator
pip install "aws-lambda-powertools[parser]"

# SAM template
Globals:
  Function:
    Handler: index.handler
    Runtime: python3.13
    Environment:
      Variables:
        POWERTOOLS_SERVICE_NAME: contact-form
        POWERTOOLS_LOG_LEVEL: INFO
```

## Logger: structured logging

Por defecto, `print()` en Lambda va a CloudWatch como texto plano. Logger
de Powertools emite JSON estructurado (parseable por CloudWatch Logs Insights).

```python
from aws_lambda_powertools import Logger

logger = Logger()

def contact_handler(event, context):
    logger.info('Received contact form', extra={'email': event['email']})
    logger.error('DynamoDB write failed', exc_info=True)  # con traceback
    logger.warning('Throttled on SES', extra={'attempt': 2})
```

Decorator `@logger.inject_lambda_context` agrega automaticamente:
- `function_name`
- `aws_request_id` (correlation ID)
- `timestamp`
- `log_level`

```python
@logger.inject_lambda_context
def contact_handler(event, context):
    logger.info('Starting')  # ya tiene aws_request_id en el output
```

Output JSON:

```json
{
  "level": "INFO",
  "location": "index.contact_handler:15",
  "message": "Starting",
  "timestamp": "2026-05-13T14:32:10.123Z",
  "service": "contact-form",
  "aws_request_id": "abc-123-def"
}
```

## Tracer: X-Ray segments

Registra traces de tu Lambda y servicios que llama (DynamoDB, SES, etc).

```python
from aws_lambda_powertools import Tracer

tracer = Tracer()
tracer.put_annotation('env', 'prod')  # filtrable en X-Ray
tracer.put_metadata('contact_id', contact_id)  # searchable

@tracer.capture_lambda_handler
def contact_handler(event, context):
    # Trace automatica de la invocacion
    contact_data = tracer.capture_dict('validate', validate_form, event)
    tracer.capture_dict('save_to_db', save_to_dynamodb, contact_data)
```

Decorator `@tracer.capture_lambda_handler` wrappea el handler con segment.
Child segments (`capture_dict`, `capture_method`) rastrean subcalls.

Boto3 integration automatica: si tienes `client = boto3.client('dynamodb')`
dentro del tracer scope, el tracer auto-instrumenta la llamada DynamoDB
(sin cambios de codigo).

```python
import boto3
from aws_lambda_powertools import Tracer

tracer = Tracer()
dynamodb = boto3.resource('dynamodb')  # auto-traced

@tracer.capture_lambda_handler
def contact_handler(event, context):
    table = dynamodb.Table('contacts')
    table.put_item(Item={'id': 'xyz'})  # segment aparece en X-Ray
```

## Metrics: CloudWatch Embedded Metrics

Emite metricas a CloudWatch en formato EMF (Embedded Metric Format).

```python
from aws_lambda_powertools import Metrics

metrics = Metrics()

@metrics.log_cold_start_metric
@tracer.capture_lambda_handler
@logger.inject_lambda_context
def contact_handler(event, context):
    metrics.add_metric(name='ContactProcessed', unit='Count', value=1)
    metrics.add_metadata(key='service_name', value='contact-form')
    
    # Opcional: dimensiones (para agrupar metricas)
    metrics.add_metadata(key='processing_type', value='form_submission')
```

Output JSON (especial format para CloudWatch):

```json
{
  "_aws": {
    "Timestamp": 1715594530000,
    "CloudWatchMetrics": [
      {
        "Namespace": "contact-form",
        "Metrics": [
          {"Name": "ContactProcessed", "Unit": "Count"}
        ]
      }
    ]
  },
  "ContactProcessed": 1,
  "processing_type": "form_submission"
}
```

CloudWatch parsea esto y crea metricas queryables.

## Parser/Validator: Pydantic v2

Valida eventos con Pydantic, auto-parsea JSON, type-safe.

```python
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from aws_lambda_powertools.utilities.parser import parse

class ContactForm(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=10)
    service: str  # one of: 'web', 'mobile', 'backend'
    company: Optional[str] = None
    budget: Optional[float] = None

def contact_handler(event, context):
    try:
        # Parse + validate automaticamente
        form = parse(event=event['body'], model=ContactForm)
        
        # Ya tipado, acceso seguro
        logger.info(f'Form from {form.email}')
        
    except ValidationError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'errors': e.errors()})
        }
```

Pydantic v2 soporte:
- `EmailStr` para validar formato email
- `Field(...)` con constraints (min_length, regex, etc.)
- `validator` decorators para logica custom
- JSON schema generation para OpenAPI

### Validator custom

```python
from pydantic import field_validator

class ContactForm(BaseModel):
    email: EmailStr
    budget: Optional[float] = None
    
    @field_validator('budget')
    @classmethod
    def budget_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('budget must be positive')
        return v
```

## Idempotency: retry-safe operations

Lambda retry politica puede duplicar invocaciones. Idempotency
wrapper memcaches results para evitar duplicacion.

```python
from aws_lambda_powertools.utilities.idempotency import idempotent

# Requiere tabla DynamoDB o cache local
from aws_lambda_powertools.idempotency.dynamodb import DynamoDBPersistence

persistence = DynamoDBPersistence(table_name='idempotency')

@idempotent(persistence=persistence)
def save_contact(contact_id, name, email):
    # Si llamada con mismo idempotency_key es retry, retorna cached result
    return {'contactId': contact_id, 'status': 'saved'}

def handler(event, context):
    # Pasar idempotency_key en event
    result = save_contact(
        contact_id='abc123',
        name='Pablo',
        email='pablo@example.com',
        idempotency_key=event['requestContext']['requestId']
    )
```

Para contact-form, usar AWS request ID como key:

```python
@idempotent(persistence=persistence)
def process_form(form_data):
    # Llamar desde handler pasando context.aws_request_id
    return save_to_dynamodb(form_data)

def handler(event, context):
    form = parse(event['body'], ContactForm)
    return process_form(form, idempotency_key=context.aws_request_id)
```

## Ejemplo completo: contact-form con todos los decorators

```python
import json
from pydantic import BaseModel, EmailStr
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.parser import parse
from aws_lambda_powertools.utilities.data_classes.api_gateway_event import APIGatewayProxyEvent

logger = Logger()
tracer = Tracer()
metrics = Metrics()

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str
    service: str
    company: str | None = None

@metrics.log_cold_start_metric
@tracer.capture_lambda_handler
@logger.inject_lambda_context
def handler(event: APIGatewayProxyEvent, context):
    """Contact form handler con validacion, logging, tracing, metricas."""
    
    try:
        # Parse + validate
        form = parse(event.json_body, ContactForm)
        logger.info('Form parsed', extra={'email': form.email})
        
        # Trace: validate Turnstile token
        token = event.headers.get('X-Turnstile-Token')
        is_valid = tracer.capture_dict('validate_turnstile', validate_turnstile, token)
        
        if not is_valid:
            logger.warning('Invalid Turnstile token')
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'bot detected'})
            }
        
        # Trace: save to DynamoDB
        contact_id = tracer.capture_dict('save_contact', save_contact, form.dict())
        
        # Trace: send email via SES
        tracer.capture_dict('send_notification', send_email, form.email)
        
        # Metrics
        metrics.add_metric('ContactSubmitted', unit='Count', value=1)
        
        logger.info('Contact saved', extra={'contactId': contact_id})
        
        return {
            'statusCode': 201,
            'body': json.dumps({'contactId': contact_id})
        }
    
    except Exception as e:
        logger.exception('Unhandled error in handler')
        metrics.add_metric('SubmissionError', unit='Count', value=1)
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'internal server error'})
        }
```

## Import order (best practices)

```python
# 1. Standard library
import json
from typing import Optional

# 2. Third-party (AWS SDK)
import boto3

# 3. AWS Powertools
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.parser import parse

# 4. Local imports
from src.models import ContactForm
from src.services import save_contact, send_email

# 5. Global initialization (top-level, no inside handler)
logger = Logger()
tracer = Tracer()
metrics = Metrics()

boto3_dynamodb = boto3.resource('dynamodb')
```

Todos los `Logger()`, `Tracer()`, `Metrics()` son singletons (reutilizables).

Verificado a fecha 2026-05-13.
