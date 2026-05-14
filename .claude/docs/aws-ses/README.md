# AWS SES knowledge base

> Conocimiento consolidado sobre AWS Simple Email Service para enviar
> notificaciones transaccionales desde Lambda en us-west-2. Cada nodo
> cubre un tema; navegar por relevancia.

## Cuando leer cada archivo

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Arquitectura: SES v1 vs v2, regiones, tipos de envio | [01-architecture.md](./01-architecture.md) | Entender opciones de API y limites de SES |
| Sandbox vs Production: limites, acceso, timings | [02-sandbox-to-production.md](./02-sandbox-to-production.md) | Solicitar acceso a produccion; cuotas iniciales |
| Domain verification: DKIM, SPF, DMARC en Cloudflare | [03-domain-verification-dns.md](./03-domain-verification-dns.md) | Configurar registros DNS antes de enviar emails |
| Python boto3: send_email, SendTemplatedEmail, errores | [04-send-email-python.md](./04-send-email-python.md) | Codigo completo para Lambda con manejo de errores |
| HTML email: MJML, cross-client, dark mode, responsive | [05-html-email-best-practices.md](./05-html-email-best-practices.md) | Disenar templates que se vean bien en Gmail/Outlook |
| Bounce/Complaint: auto-suppression, SNS, reputacion | [06-bounce-complaint-handling.md](./06-bounce-complaint-handling.md) | Monitorear entregas, mantener sender reputation |
| SAM template: ConfigurationSet, event destinations, IAM | [07-deployment-sam.md](./07-deployment-sam.md) | Infrastructure-as-code para SES + Lambda |
| Monitoring: dashboard, metricas, CloudWatch alarms | [08-monitoring-reputation.md](./08-monitoring-reputation.md) | Alertas cuando bounce/complaint rates suben |
| Cost breakdown 2026: SES vs SendGrid vs Resend | [09-cost-comparison-2026.md](./09-cost-comparison-2026.md) | Por que SES para este portfolio (bajo volumen) |

## Reglas criticas

- NUNCA enviar emails desde direccion no-verificada en SES
  (MailFromDomainNotVerified error).
- NUNCA saltarse DKIM + SPF + DMARC: mejora deliverability
  e inbox rate dramaticamente.
- SIEMPRE habilitar account-level suppression para auto-block
  bounces y complaints.
- SIEMPRE monitorear bounce rate (< 5%) y complaint rate
  (< 0.1%) — AWS suspende accounts con rates altos.
- NUNCA hardcodear AWS credentials en codigo. Usar IAM role
  en Lambda.
- Sandbox limita a 200 emails/24h: solicitar production access
  (24-48h turnaround) ANTES de enviar emails en produccion.

## Quick start: enviar primer email desde Lambda

```bash
# 1. Verificar dominio en SES (via AWS Console)
# 2. Configurar DKIM + SPF en Cloudflare (ver 03-domain-verification-dns.md)
# 3. Solicitar production access (ver 02-sandbox-to-production.md)
# 4. Esperar aprobacion (24-48h)
# 5. Copiar codigo de 04-send-email-python.md a Lambda handler
# 6. Deployar con SAM (ver 07-deployment-sam.md)
# 7. Probar con evento form de contacto
# 8. Monitorear reputation dashboard (ver 08-monitoring-reputation.md)
```

## Caso de uso del portfolio (Mayo 2026)

- Volumen: 50-200 emails/mes (bajo)
- Tipo: Transactional (notificacion al owner)
- From: no-reply@the-full-stack.com (domain verificado)
- To: pacg1991@gmail.com (owner personal)
- Region: us-west-2 (Oregon)
- Costo estimado: $0.02/mes ($0.10 per 1000 emails, free tier 3000/mes)
- Alternative considerada: Resend (mejor DX, pero SES integra con AWS)

## Estado actual (Mayo 2026)

- SES setup: en planificacion
- Domain verification: pendiente (requiere records DKIM/SPF/DMARC en Cloudflare)
- Production access: pendiente (sandbox -> production)
- Lambda integration: pendiente (boto3 client en Python 3.13)
- Monitoring: setup basico (CloudWatch metrics + SNS)
