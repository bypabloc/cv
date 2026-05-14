# Enviar emails con boto3: SendEmail, error handling, templates

> Codigo completo Python 3.13 para Lambda con SES client.
> Ejemplos de SendEmail, SendTemplatedEmail, y manejo de errores.

## Ejemplo basico: SendEmail

```python
import boto3
from botocore.exceptions import ClientError

ses = boto3.client('ses', region_name='us-west-2')

def send_contact_notification(name: str, email: str, message: str) -> dict:
    """
    Envia email de notificacion al owner cuando recibe un contacto.
    
    :param name: Nombre del contacto
    :param email: Email del contacto
    :param message: Mensaje del contacto
    :return: {'success': bool, 'message_id': str, 'error': str | None}
    """
    try:
        response = ses.send_email(
            Source='no-reply@the-full-stack.com',
            Destination={
                'ToAddresses': ['pacg1991@gmail.com'],
            },
            Message={
                'Subject': {
                    'Data': f'Nuevo contacto: {name}',
                    'Charset': 'UTF-8',
                },
                'Body': {
                    'Text': {
                        'Data': f'Nombre: {name}\nEmail: {email}\n\nMensaje:\n{message}',
                        'Charset': 'UTF-8',
                    },
                    'Html': {
                        'Data': f'''
                        <html>
                            <body>
                                <h2>Nuevo contacto</h2>
                                <p><strong>Nombre:</strong> {name}</p>
                                <p><strong>Email:</strong> {email}</p>
                                <p><strong>Mensaje:</strong></p>
                                <p>{message}</p>
                            </body>
                        </html>
                        ''',
                        'Charset': 'UTF-8',
                    },
                },
            },
        )
        return {
            'success': True,
            'message_id': response['MessageId'],
            'error': None,
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        return {
            'success': False,
            'message_id': None,
            'error': f'{error_code}: {error_msg}',
        }
```

## Manejo de errores comunes

```python
def send_email_safe(source: str, to: str, subject: str, body_html: str) -> dict:
    """
    Envio con error handling detallado.
    """
    try:
        response = ses.send_email(
            Source=source,
            Destination={'ToAddresses': [to]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': body_html, 'Charset': 'UTF-8'},
                },
            },
        )
        return {'success': True, 'message_id': response['MessageId']}

    except ClientError as e:
        error_code = e.response['Error']['Code']

        # Errores especificos de SES
        if error_code == 'MessageRejected':
            # Causa comun: sender no verificado, o recipient no verificado (sandbox)
            return {'success': False, 'reason': 'sender_or_recipient_not_verified'}

        elif error_code == 'MailFromDomainNotVerified':
            # El dominio del "From" no esta verificado en SES
            return {'success': False, 'reason': 'domain_not_verified'}

        elif error_code == 'ConfigurationSetDoesNotExist':
            # Si usas configuration sets (para tracking), el set no existe
            return {'success': False, 'reason': 'config_set_missing'}

        elif error_code == 'AccountSendingPausedException':
            # Cuenta en sandbox o bounce rate demasiado alto
            return {'success': False, 'reason': 'account_sending_paused'}

        elif error_code == 'InvalidParameterValue':
            # Email malformado, charset invalido, etc.
            return {'success': False, 'reason': 'invalid_parameter'}

        else:
            # Error desconocido
            return {
                'success': False,
                'reason': 'unknown',
                'error': str(e),
            }
```

## Lambda Handler (integracion completa)

```python
import json
import boto3
from botocore.exceptions import ClientError

ses = boto3.client('ses', region_name='us-west-2')

def lambda_handler(event, context):
    """
    Handler para API Gateway POST /contact.
    
    Body esperado:
    {
        "name": "Pablo",
        "email": "user@example.com",
        "message": "Hola, me interesa...",
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
                'body': json.dumps({'error': 'Missing required fields'}),
            }

        # Construir HTML del email
        html_body = f'''
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2>Nuevo contacto desde {subdomain}</h2>
                    <hr />
                    <p><strong>Nombre:</strong> {html_escape(name)}</p>
                    <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
                    <p><strong>Subdomain:</strong> {subdomain}</p>
                    <hr />
                    <h3>Mensaje:</h3>
                    <blockquote style="border-left: 4px solid #ddd; padding-left: 1em;">
                        {html_escape(message).replace(chr(10), '<br />')}
                    </blockquote>
                </div>
            </body>
        </html>
        '''

        # Enviar via SES
        response = ses.send_email(
            Source='no-reply@the-full-stack.com',
            Destination={'ToAddresses': ['pacg1991@gmail.com']},
            Message={
                'Subject': {
                    'Data': f'Nuevo contacto: {name} via {subdomain}',
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

        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message_id': response['MessageId'],
            }),
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f'SES Error: {error_code} - {e.response["Error"]["Message"]}')

        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f'Email service unavailable: {error_code}',
            }),
        }

    except Exception as e:
        print(f'Unexpected error: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
            }),
        }


def html_escape(text: str) -> str:
    """Escapa caracteres especiales HTML para evitar XSS."""
    return (
        text.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )
```

## SendTemplatedEmail (usando templates SES)

Si creas templates en SES Console:

```python
def send_templated_contact_notification(
    name: str,
    email: str,
    message: str,
    subdomain: str,
) -> dict:
    """
    Envio con template SES (template_name: ContactNotification).
    Template data pasa como JSON string.
    """
    try:
        response = ses.send_templated_email(
            Source='no-reply@the-full-stack.com',
            Destination={'ToAddresses': ['pacg1991@gmail.com']},
            Template='ContactNotification',  # Nombre del template en SES
            TemplateData=json.dumps({
                'name': name,
                'email': email,
                'message': message,
                'subdomain': subdomain,
            }),
        )
        return {
            'success': True,
            'message_id': response['MessageId'],
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'TemplateDoesNotExist':
            return {
                'success': False,
                'reason': 'template_not_found',
                'suggestion': 'Crea el template "ContactNotification" en SES Console',
            }
        else:
            return {
                'success': False,
                'reason': error_code,
            }
```

## IAM Policy (permisos minimos)

Para una Lambda que envia emails via SES:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ses:FromAddress": "no-reply@the-full-stack.com"
        }
      }
    }
  ]
}
```

**Explicacion**:
- `ses:SendEmail` + `ses:SendRawEmail`: permisos para enviar
- `Condition`: solo desde la direccion verificada (restrictivo)
- NUNCA usar `"Action": "ses:*"` (demasiado amplio)

## Idempotency y message_id

Cada email recibe un `MessageId` unico:

```python
response = ses.send_email(...)
message_id = response['MessageId']

# Guardar en DB para audit/retry logic
# Si la Lambda reintenta, puedes detectar duplicate usando message_id
```

## Testing local (con moto o Localstack)

Para testear sin credentials AWS:

```python
from moto import mock_ses

@mock_ses
def test_send_email():
    client = boto3.client('ses', region_name='us-west-2')
    
    # Pre-verify la direccion en mock
    client.verify_email_identity(EmailAddress='no-reply@the-full-stack.com')
    client.verify_email_identity(EmailAddress='pacg1991@gmail.com')
    
    # Enviar
    response = client.send_email(
        Source='no-reply@the-full-stack.com',
        Destination={'ToAddresses': ['pacg1991@gmail.com']},
        Message={
            'Subject': {'Data': 'Test'},
            'Body': {'Text': {'Data': 'Test message'}},
        },
    )
    
    assert 'MessageId' in response
    print(f"Test email sent with ID: {response['MessageId']}")
```

## Fuentes

- [boto3 SES send_email API](https://docs.aws.amazon.com/ses/latest/APIReference/API_SendEmail.html)
- [boto3 SES send_templated_email API](https://docs.aws.amazon.com/ses/latest/APIReference/API_SendTemplatedEmail.html)
- [AWS SDK Code Examples: SES Python](https://docs.aws.amazon.com/code-library/latest/ug/python_3_ses_code_examples.html)

**Verificado 2026-05-13**
