# SES setup - the-full-stack.com

> Estado actual: **production access GRANTED en us-east-1** (case `173472640000887`).
> Esta spec quedo casi vacia porque la configuracion DKIM/SPF/DMARC se hizo
> previamente. Este documento es para referencia + verificacion.

## Resumen

| Item | Valor | Estado |
|------|-------|--------|
| Region | `us-east-1` | ✅ |
| Account | `637423614564` | ✅ |
| Domain identity | `the-full-stack.com` | ✅ Verified |
| Email identity | `the.full.stack.tech@gmail.com` | ✅ Verified (legacy) |
| Production access | Case `173472640000887` | ✅ GRANTED |
| Daily quota | 50,000 emails/day | ✅ |
| Send rate | 14 emails/seg | ✅ |
| Enforcement status | HEALTHY | ✅ |
| Mail type | TRANSACTIONAL | ✅ |
| Dedicated IP auto-warmup | Enabled | ✅ |
| Suppression list | BOUNCE + COMPLAINT auto-managed | ✅ |

## Verificacion (idempotente)

```bash
# Identidades verificadas
aws sesv2 list-email-identities --region us-east-1 \
  --query 'EmailIdentities[*].[IdentityName,VerificationStatus,SendingEnabled]'

# Account-level (sandbox, production, quota)
aws sesv2 get-account --region us-east-1

# Send quota actual
aws sesv2 get-account --region us-east-1 \
  --query 'SendQuota.[Max24HourSend,MaxSendRate,SentLast24Hours]'
```

## DKIM (Cloudflare DNS)

3 CNAMEs del DKIM autogenerados por SES estan en Cloudflare DNS para
`the-full-stack.com`. Para verificar:

```bash
# Inspeccionar DKIM tokens en SES
aws sesv2 get-email-identity --email-identity the-full-stack.com \
  --region us-east-1 --query 'DkimAttributes'
```

Si vieras `Status: SUCCESS` y `Tokens` no vacios -> DKIM esta OK en Cloudflare.

## SPF + DMARC

SPF TXT (`v=spf1 include:amazonses.com -all`) y DMARC TXT
(`v=DMARC1; p=quarantine; rua=mailto:...`) ya estan en Cloudflare DNS
desde antes (no es parte de esta spec).

## Email sender (configurado)

| Variable | Valor |
|----------|-------|
| `EMAIL_FROM` (SSM `/portfolio/ses-from-address`) | `no-reply@the-full-stack.com` |
| `OWNER_EMAIL` (SSM `/portfolio/owner-email`) | `pacg1991@gmail.com` |

Configurados en SPEC-000 + verificados como SES identities en us-east-1.

## Mail Tester (validacion deliverability futura)

Cuando el frontend este live y se envie el primer email real:

1. Ir a https://www.mail-tester.com/
2. Copiar el email destinatario generado
3. Enviar un contact_form desde el portfolio apuntando a ese email
4. Ver el score. Objetivo: >= 8/10

NO disponible en esta spec (requiere SPEC-012 + frontend live).

## SES Bounce/Complaint handling (futuro, no en MVP)

Para limit increase >100k emails/day, configurar SNS topic + Lambda que
escuche bounces/complaints y popule supresion. NO necesario para portfolio
volumen actual (~200 emails/mes).
