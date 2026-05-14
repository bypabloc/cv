# Bounce/Complaint handling: monitorear entregas y reputacion

> Auto-suppression de SES, SNS notifications, bounce types, y management
> de sender reputation.

## Tipos de bounce

SES detecta dos tipos de problemas en entregas:

### Bounce: Hard (permanente)

Email fue rechazado permanentemente:

| Razon | Codigo SES | Accion | Reputacion |
|-------|-----------|--------|-----------|
| Mailbox no existe | InvalidAddress | No reintentar, marcar como invalido | Impacto alto |
| Dominio no existe | InvalidDomain | No reintentar | Impacto alto |
| Rejected by ISP (blacklist) | RejectionRejected | Hold x 5 intentos, luego dar up | Impacto medio |
| Account deactivated | AccountProblem | No reintentar | Impacto alto |
| Mensaje rechazado por policy ISP | MailboxDisabled | No reintentar | Impacto alto |

**Hard bounce**: NO reintentar. Indicativo de una lista de emails mala.

### Bounce: Soft (temporal)

Email fue rechazado temporalmente:

| Razon | Codigo SES | Accion | Reputacion |
|-------|-----------|--------|-----------|
| Mailbox lleno | InsufficientStorage | Reintentar en 1h, luego 4h, 24h | Impacto bajo |
| Servidor temporalmente no disponible | ServiceUnavailable | Reintentar exponencial | Impacto bajo |
| Rate limit del ISP | Throttling | Exponential backoff | Impacto bajo |
| Problemas temporales | TemporaryFailure | Reintentar | Impacto bajo |

**Soft bounce**: Reintentar. Generalmente se resuelve solo.

## Complaint: email marcado como spam

Cuando un recipient marca tu email como spam en Gmail/Outlook:

```
Usuario recibe email → marca "Report spam" → Gmail/Outlook → SES
  ↓
SES detecta complaint → SNS topic → Lambda
  ↓
Lambda: agregar a suppression list
  ↓
Nunca mas enviar a ese recipient (SES rechaza automaticamente)
```

**Impacto**: 1 complaint puede desactivar toda una account si superas 0.1%.

## Auto-suppression: SES maneja bounces/complaints automaticamente

### Habilitar account-level suppression

En SES Console (us-west-2):

1. Navigate to "Account dashboard"
2. Under "Suppression list", toggle "Enable account-level suppression"
3. Check "Bounces" + "Complaints"

**Resultado**: SES mantiene automaticamente una lista de emails con hard bounce o complaint.
Intentos de envio a esos emails se rechazan con error `MessageRejected`.

### Verificar suppression list

```bash
# CLI command
aws sesv2 get-suppressed-destination \
  --email-address "user@example.com" \
  --region us-west-2

# Response (si esta suppressed)
{
  "SuppressedDestination": {
    "EmailAddress": "user@example.com",
    "Reason": "BOUNCE",
    "LastUpdateTime": "2026-05-13T10:30:00Z",
    "Attributes": {
      "BounceType": "Permanent",
      "BounceSubType": "General"
    }
  }
}
```

## SNS notifications: capturar bounces y complaints

Para aplicaciones criticas (auditar todos los bounces), configurar SNS topics:

### Crear configuration set (en SES)

```bash
aws sesv2 create-configuration-set \
  --configuration-set-name portfolio-contact \
  --region us-west-2
```

### Crear SNS topic y subscribir Lambda

```bash
# Crear topic
aws sns create-topic --name ses-bounces-complaints --region us-west-2
# Output: TopicArn: arn:aws:sns:us-west-2:123456:ses-bounces-complaints

# Subscribir Lambda handler
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:123456:ses-bounces-complaints \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:us-west-2:123456:function:handle-ses-events \
  --region us-west-2
```

### Agregar event destination en configuration set

```bash
aws sesv2 create-configuration-set-event-destination \
  --configuration-set-name portfolio-contact \
  --event-destination-name bounces-topic \
  --event-types BOUNCE COMPLAINT \
  --sns-destination TopicArn=arn:aws:sns:us-west-2:123456:ses-bounces-complaints \
  --region us-west-2
```

### Lambda handler para procesar eventos

```python
import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('email-suppression-list')

def lambda_handler(event, context):
    """
    Procesa eventos de bounce/complaint desde SNS/SES.
    
    Event structure (SNS message):
    {
      "Records": [{
        "Sns": {
          "Message": "{...JSON...}"
        }
      }]
    }
    """
    try:
        for record in event.get('Records', []):
            sns_message = json.loads(record['Sns']['Message'])
            message_type = sns_message.get('eventType')

            if message_type == 'Bounce':
                handle_bounce(sns_message)
            elif message_type == 'Complaint':
                handle_complaint(sns_message)

        return {'statusCode': 200, 'body': 'OK'}

    except Exception as e:
        print(f'Error: {str(e)}')
        return {'statusCode': 500, 'body': str(e)}


def handle_bounce(message: dict):
    """Procesa bounce notification."""
    bounce = message.get('bounce', {})
    bounce_type = bounce.get('bounceType')  # 'Transient' o 'Permanent'
    bounce_subtype = bounce.get('bounceSubType')

    for recipient in bounce.get('bouncedRecipients', []):
        email = recipient['emailAddress']
        status = recipient['status']
        diagnostic = recipient.get('diagnosticCode', '')

        print(f'Bounce {bounce_type}: {email} - {status} - {diagnostic}')

        if bounce_type == 'Permanent':
            # Marcar como invalido en DB
            table.put_item(Item={
                'email': email,
                'reason': f'bounce_{bounce_subtype}',
                'timestamp': int(time.time()),
            })


def handle_complaint(message: dict):
    """Procesa complaint notification."""
    complaint = message.get('complaint', {})

    for recipient in complaint.get('complainedRecipients', []):
        email = recipient['emailAddress']
        complaint_feedback_type = recipient.get('complaintFeedbackType', 'unknown')

        print(f'Complaint from {email}: {complaint_feedback_type}')

        # Marcar como complained
        table.put_item(Item={
            'email': email,
            'reason': f'complaint_{complaint_feedback_type}',
            'timestamp': int(time.time()),
        })
```

## Monitoreo de rates

### Bounce rate > 5%

AWS coloca la account "Under Review" si bounce rate supera 5%.

**Causas**:
- Lista de emails sucia (muchas direcciones invalidas)
- Harvesting o scraped lists
- Form validation incompleta

**Solucion**:
- Validar emails en forma (regex + verification link)
- Limpiar lista de bounces existentes
- Re-verificar addresses con double opt-in

### Complaint rate > 0.1%

AWS **suspende la account** si superas 0.1% complaint rate.

**Causas**:
- Sending without consent (spam perception)
- Subject line confuso o engañoso
- Demasiada frecuencia

**Solucion**:
- Confirmation email despues de form submission
- Agregar "unsubscribe" link en emails (legalmente requerido en muchas jurisdicciones)
- Respectar frequency (max 1-2 emails/semana)

## CloudWatch metrics

SES publica automaticamente metricas a CloudWatch:

```bash
# Ver metrics disponibles
aws cloudwatch list-metrics \
  --namespace AWS/SES \
  --region us-west-2
```

Metricas importantes:

| Metrica | Que significa |
|---------|--------|
| Send | Emails exitosamente aceptados por SES |
| Bounce | Total bounces (hard + soft) |
| Complaint | Emails marcados como spam |
| Delivery | Emails entregados al ISP |
| Open | Emails abiertos (si tracking habilitado) |
| Click | Clicks en links (si tracking habilitado) |
| BounceRate | (Bounces / Send) * 100 |
| ComplaintRate | (Complaints / Send) * 100 |

### CloudWatch Alarm (bounce rate high)

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_alarm(
    AlarmName='SES-HighBounceRate',
    MetricName='Reputation.BounceRate',
    Namespace='AWS/SES',
    Statistic='Average',
    Period=3600,  # 1 hour
    EvaluationPeriods=1,
    Threshold=5.0,  # 5%
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-west-2:123456:alerts'],
)
```

## Best practices de reputacion

1. **Validar emails en form**:
   - Regex basico: `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`
   - Verification email: enviar link para confirmar ownership

2. **Mantener lista limpia**:
   - Limpiar bounces periodicamente
   - NO re-enviar a emails con bounce hard
   - Usar DKIM + SPF + DMARC

3. **Respetar recipients**:
   - Solo enviar a quien consintio explicitamente
   - Incluir unsubscribe link (OBLIGATORIO legalmente)
   - No enviar demasiado frecuente

4. **Monitorear continuamente**:
   - Revisar CloudWatch metrics diariamente
   - Configurar alarms para bounce > 3% y complaint > 0.05%
   - Responder rapido si rates suben

5. **Para bajo volumen (como este portfolio)**:
   - Riesgo muy bajo (200 emails/mes a 1 recipient = 0% bounce/complaint)
   - Account-level suppression es suficiente
   - SNS/Lambda opcional (pero good practice)

## Fuentes

- [AWS SES: Bounce and Complaint Notifications](https://docs.aws.amazon.com/ses/latest/dg/notification-contents.html)
- [AWS SES: Suppression List Management](https://docs.aws.amazon.com/ses/latest/dg/manage-suppression-list.html)
- [AWS SES: Bounce/Complaint Handling (AWS Messaging Blog)](https://aws.amazon.com/blogs/messaging-and-targeting/handling-bounces-and-complaints/)
- [AWS SES: Reputation Dashboard](https://docs.aws.amazon.com/ses/latest/dg/reputation-dashboard-dg.html)

**Verificado 2026-05-13**
