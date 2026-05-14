# SES Architecture: v1 vs v2, regiones, tipos de envio

> Opciones de arquitectura de SES: cual API usar, donde deployar, como
> enviar emails.

## SES API v1 vs v2 (RECOMENDACION 2026)

AWS maneja dos versiones de la API de SES:

| Aspecto | v1 (Legacy) | v2 (Recomendado) |
|--------|-----------|----------------|
| **Status 2026** | Soportada pero legacy | Recomendada para nuevos proyectos |
| **Endpoint** | `ses.region.amazonaws.com` | `email.region.amazonaws.com` |
| **Metodo principal** | SendEmail, SendRawEmail | SendEmail, SendBulkEmail, SendRawEmail |
| **SendBulkEmail** | No disponible | Si (optimizado para bulk) |
| **DX (boto3)** | Funciona igual | Funciona igual |
| **Reputacion** | Soportada | Mejorada (mejor tracking) |
| **Documentacion** | Completa pero envejecida | Activa, se recomienda leer v2 docs |

Para este portfolio (transactional, bajo volumen): ambas APIs funcionan
identicamente. Recomendacion: **usar boto3 SES v2** porque AWS la soportara mas
tiempo y los ejemplos de 2026 usan v2.

## Regiones disponibles (Mayo 2026)

SES esta disponible en 11 regiones AWS. Cada region tiene su propia sandbox,
cuotas, y suppression lists.

| Region | Endpoint | Uso |
|--------|----------|-----|
| us-east-1 | ses.us-east-1.amazonaws.com | Primary, US East Coast |
| **us-east-1** | ses.us-east-1.amazonaws.com | **Portfolio: Oregon (bajo latency a La Costa)** |
| eu-west-1 | ses.eu-west-1.amazonaws.com | Europa (Irlanda) |
| eu-central-1 | ses.eu-central-1.amazonaws.com | Europa (Frankfurt) |
| ap-southeast-1 | ses.ap-southeast-1.amazonaws.com | Asia Pacifico (Singapur) |
| ap-southeast-2 | ses.ap-southeast-2.amazonaws.com | Australia (Sydney) |
| ap-northeast-1 | ses.ap-northeast-1.amazonaws.com | Asia (Japon) |
| ca-central-1 | ses.ca-central-1.amazonaws.com | Canada |
| sa-east-1 | ses.sa-east-1.amazonaws.com | America Latina (Sao Paulo) |
| us-gov-west-1 | ses.us-gov-west-1.amazonaws.com | AWS GovCloud (US Government) |
| cn-north-1 | ses.cn-north-1.amazonaws.com | AWS China |

**Para este portfolio**: us-east-1 es ideal (bajo latency, infraestructura
madura, soporte SES completo). La Consola de SES y todas las features estan
disponibles en us-east-1.

## Tipos de envio de email

SES soporta 4 metodos para enviar emails. Cada uno tiene un caso de uso:

### 1. SendEmail (standard)

```python
client.send_email(
    Source='no-reply@the-full-stack.com',
    Destination={'ToAddresses': ['pacg1991@gmail.com']},
    Message={
        'Subject': {'Data': 'Nuevo contacto'},
        'Body': {
            'Text': {'Data': 'Plain text body'},
            'Html': {'Data': '<h1>HTML body</h1>'}
        }
    }
)
```

**Uso**: Envios individuales, transaccional, notificaciones.
**Ventajas**: API simple, soporta hasta 50 recipients.
**Limites**: Max 40MB email size.

### 2. SendBulkEmail (bulk optimizado)

```python
client.send_bulk_email(
    FromEmailAddress='no-reply@the-full-stack.com',
    DefaultDestination={'ToAddresses': ['user1@example.com', 'user2@example.com']},
    Template='ContactNotification',
    DefaultTemplateData='{"name": "Pablo"}'
)
```

**Uso**: Envios masivos a muchos recipients, newsletters, campaigns.
**Ventajas**: Optimizado para volumen alto, mejor manejo de errores por recipient.
**Limites**: Max 1000 recipients por request.

### 3. SendRawEmail (MIME custom)

```python
client.send_raw_email(
    RawMessage={'Data': mime_string},
    Source='no-reply@the-full-stack.com'
)
```

**Uso**: Emails con headers custom, adjuntos complejos, firmas MIME.
**Ventajas**: Control total del mensaje.
**Limites**: Responsabilidad del dev de validar MIME completo.

### 4. SendTemplatedEmail (templates server-side)

```python
client.send_templated_email(
    Source='no-reply@the-full-stack.com',
    Destination={'ToAddresses': ['pacg1991@gmail.com']},
    Template='ContactNotification',
    TemplateData='{"name": "Pablo", "email": "contact@example.com"}'
)
```

**Uso**: Emails personalizados desde templates SES.
**Ventajas**: Separation de logica (template en SES, data en Lambda).
**Limites**: Requiere crear template en SES console antes.

## Recomendacion para este portfolio

**SendEmail** es suficiente:
- Bajo volumen (50-200 emails/mes)
- Unico recipient (notificacion al owner)
- Lambda arma el body HTML en el codigo
- No requiere template management

Si aumenta volumen o se necesita personalizacion: considerar **SendTemplatedEmail**
para separar template de logica de envio.

## Limites de SES (Mayo 2026)

| Limite | Valor | Notas |
|--------|-------|-------|
| Max email size | 40 MB | Incluye attachments |
| Max recipients/email | 50 | (ToAddresses + CcAddresses + BccAddresses) |
| Max templates | 20,000 per region | |
| Max template size | 500 KB | |
| Email charset | UTF-8 recomendado | Latin-1 soportado |
| Sandbox daily limit | 200 emails/24h | Hasta solicitar production |
| Sandbox rate limit | 1 email/segundo | |

## Pricing (us-east-1, Mayo 2026)

| Item | Costo |
|------|-------|
| Emails enviados | $0.10 per 1000 emails |
| Data transfer | $0.12 per GB |
| VirtualDeliverabilityManager | $0.07 per 1000 emails (opcional) |
| Free tier (12 meses) | 3000 message charges/mes |

Para 200 emails/mes: **$0.02/mes** (dentro de free tier).

## Flujo tipico de email en el portfolio

```
User Submit Form (HTML/JS)
    ↓
API Gateway / Lambda Handler
    ↓
Validar form data (email, nombre, mensaje)
    ↓
boto3 SES Client (us-east-1)
    ↓
SendEmail({
  From: no-reply@the-full-stack.com,
  To: pacg1991@gmail.com,
  Subject: "Nuevo contacto: {nombre} via {subdomain}",
  Body: HTML + Plain text
})
    ↓
SES Service: autenticar DKIM, validar SPF/DMARC
    ↓
Enviar via SMTP a mailbox Gmail
    ↓
Gmail: marcar como legit o spam
    ↓
Webhook SNS (bounce/complaint)
    ↓
Lambda: handle bounce/complaint → actualizar suppression list
```

## Fuentes

- [AWS SES API Reference v2](https://docs.aws.amazon.com/ses/latest/APIReference-V2/Welcome.html)
- [AWS SES Documentation](https://docs.aws.amazon.com/ses/)
- [SES Pricing 2026](https://aws.amazon.com/ses/pricing/)

**Verificado 2026-05-13**
