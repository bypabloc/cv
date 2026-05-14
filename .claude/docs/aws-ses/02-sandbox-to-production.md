# Sandbox vs Production: acceso, limites, timings

> Como salir de SES Sandbox y solicitar acceso a produccion.
> Limites, cuotas iniciales, y tiempos de aprobacion.

## SES Sandbox (estado inicial)

Cuando creas una cuenta AWS nueva, SES empieza en **Sandbox mode**. Es un
entorno de testing con restricciones severas:

| Restriccion | Limite |
|------------|--------|
| Emails/24h | 200 |
| Rate limit | 1 email/segundo |
| Recipients | Solo verified email addresses + SES mailbox simulator |
| Identities verificadas | Solo las que verificaste vos |
| Use case | Testing y development |
| Costo | Gratis (dentro de free tier) |

### Ejemplo: error en Sandbox

```python
# SES Sandbox: intento enviar a un recipient no verificado
response = client.send_email(
    Source='verified@example.com',
    Destination={'ToAddresses': ['random-person@gmail.com']},  # No verificado
    Message={...}
)

# Resultado: MessageRejected error
# "Message Rejected: Email address not verified."
```

## Production Access (flujo de solicitud)

### Paso 1: Verificar dominio (OBLIGATORIO antes de solicitar)

Antes de solicitar production access, **verifica el dominio** desde el cual
vas a enviar emails:

```bash
# En AWS SES Console (us-west-2):
# 1. Navigate to "Verified Identities"
# 2. Click "Create Identity"
# 3. Select "Domain"
# 4. Enter: the-full-stack.com
# 5. SES proporciona token de verificacion
# 6. Agrega TXT record a Cloudflare DNS
# 7. Click "Verify" (puede tardar algunos minutos)
```

Una vez verificado, el status cambia a "verified" en la console.

### Paso 2: Solicitar Production Access (via AWS Console)

En SES Console → Account Dashboard:

1. Click en el banner rojo: "Your Amazon SES account is in the sandbox"
2. Click "View Get set up page" → "Request production access"
3. Selecciona radio button: **Transactional** (porque es notificacion)
4. Website URL: `https://the-full-stack.com`
5. Additional contacts: `pacg1991@gmail.com` (solo es necesario 1)
6. Preferred language: English
7. Marcar checkbox: "I acknowledge..."
8. Click "Submit request"

**Resultado**: Aparece banner azul: "Your request is under review."

### Paso 3: Esperar aprobacion

| Fase | Tiempo estimado |
|-----|-----------------|
| AWS initial response | 24 horas |
| Aprobacion (si todo OK) | 24 horas (same as initial) |
| Denegacion (si falta info) | 24-48 horas (pueden pedir aclaraciones) |

**Total esperado**: 24-48 horas.

### Paso 4: Verificar status

En SES Console → Account Dashboard:

- Si fue aprobado: banner verde "Your account has production access"
- Si fue denegado: revisar email de AWS con razon del rechazo

## Production Access (via AWS CLI)

Alternativa: solicitar production access automaticamente desde CLI:

```bash
aws sesv2 put-account-details \
  --production-access-enabled \
  --mail-type TRANSACTIONAL \
  --website-url "https://the-full-stack.com" \
  --additional-contact-email-addresses "pacg1991@gmail.com" \
  --contact-language EN \
  --region us-west-2
```

Resultado: Output JSON con confirmacion de request enviado.

## Production Quotas (iniciales)

Una vez aprobado, recibis cuotas bases. Para **Transactional** (bajo volumen):

| Metrica | Valor inicial |
|---------|--------------|
| Emails/24h | 50,000 (para nuevas accounts) |
| Rate limit | 14 emails/segundo |
| Identities | Unlimited (puedes verificar más) |
| Suppression list | Habilitada (auto-block bounces + complaints) |

**Notas importantes**:
- AWS **puede aumentar automaticamente** las cuotas si detecta buena reputacion
- Puedes solicitar aumento manual si necesitas más via support ticket
- Las cuotas son **por region**: si deployas en otra region, necesitas solicitar
  production access nuevamente

## Criterios de aprobacion (que AWS revisa)

AWS examina tu solicitud y verifica:

1. **Website existe y es legitimo**
   - Accesible y contiene contenido real
   - No es parking page ni dominio vacio

2. **Use case is transactional, no marketing**
   - Marketing email = bulk newsletters, campaigns (requiere lista consent)
   - Transactional = notificaciones triggered by user action (mejor aprobacion)

3. **Email authentication setup**
   - DKIM configurado (SES Easy DKIM)
   - SPF record agregado al dominio
   - Idealmente DMARC tambien (best practice)

4. **No hay patrones sospechosos**
   - No usar emails con palabras "lottery", "prize", "verify account", etc.
   - No spoofing de dominios conocidos

## Rejection causes (comun)

| Razon | Solucion |
|-------|----------|
| "Website URL is not accessible" | Verifica que el domain este vivo y resolva |
| "Insufficient domain verification" | Espera a que DKIM verification se complete (puede tardar 24h) |
| "High-risk sending pattern detected" | Cambia subject line, describe mejor el caso de uso |
| "Unverified domain" | Verifica el dominio ANTES de solicitar production |
| "No contact method" | Incluye al menos 1 email valido en "Additional contacts" |

## Anti-patterns a evitar

- NUNCA solicitar production access sin verificar el dominio primero
- NUNCA cambiar el dominio o email de contacto durante el review
- NUNCA usar "Test" o "Demo" como website URL
- NUNCA marcar "Marketing" si solo necesitas transactional
- NUNCA intentar circumvent sandbox limits con multiple SES accounts

## Timeline para el portfolio (hipotetico)

```
Day 1:
  - Verificar dominio the-full-stack.com (DKIM setup in Cloudflare)
  - Solicitar production access (11:00 AM UTC)

Day 2:
  - 11:00 AM: AWS responde con aprobacion o request de info
  - Si aprobacion: Production access habilitado
  - Si request info: responder y esperar

Day 3:
  - Confirmar status en console (debe decir "production access")
  - Deployar Lambda con SES client
  - Enviar email de prueba
```

## Fuentes

- [AWS SES: Request production access](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html)
- [AWS SES: Managing sending quotas](https://docs.aws.amazon.com/ses/latest/dg/manage-sending-quotas.html)
- [AWS SES: Service quotas](https://docs.aws.amazon.com/ses/latest/dg/quotas.html)

**Verificado 2026-05-13**
