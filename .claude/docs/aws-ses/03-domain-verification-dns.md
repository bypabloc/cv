# Domain Verification: DKIM, SPF, DMARC en Cloudflare

> Como verificar la identidad del dominio y configurar autenticacion de email.
> Pasos exactos para Cloudflare DNS.

## Flujo de verificacion (3 capas de autenticacion)

Email authentication en 2026 requiere 3 capas para maxima deliverability:

```
1. Domain Verification (propriedad del dominio)
   ↓
2. SPF (autoriza que mail servers pueden enviar)
   ↓
3. DKIM (firma digital de emails)
   ↓
4. DMARC (politica de que hacer si SPF/DKIM fallan)
```

**Resultado**: Emails llegan a inbox en Gmail/Outlook, no spam.

## Paso 1: Verificar dominio en SES

### En AWS SES Console (us-east-1)

1. Navigate to "Verified Identities"
2. Click "Create Identity"
3. Select "Domain" (no "Email address")
4. Enter domain: `the-full-stack.com`
5. Click "Create Identity"

AWS genera un **verification token** (TXT record):

```
Name:  _amazonses.the-full-stack.com
Type:  TXT
Value: abc123defghijk...
```

### En Cloudflare DNS Dashboard

1. Login a [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Select domain: `the-full-stack.com`
3. Navigate to "DNS" → "Records"
4. Click "+ Add Record"
5. Fill in:
   - Type: TXT
   - Name: `_amazonses`
   - Content: `abc123defghijk...` (valor de AWS)
   - TTL: Auto
   - Proxy status: **DNS only** (CRITICO)
6. Click "Save"

Espera 5-15 minutos y vuelve a SES Console. Click "Verify" button.
Status debe cambiar a "verified".

## Paso 2: Configurar Easy DKIM (3 CNAME records)

Easy DKIM es el metodo mas simple: AWS genera las claves, tu solo agrega
3 CNAME records.

### En AWS SES Console

1. Selecciona el dominio verificado
2. Click en pestaña "DKIM"
3. Click "Create DKIM"
4. Selecciona "Easy DKIM" (default)
5. Selecciona key length: **2048-bit** (recomendado 2026)
6. Click "Confirm"

AWS genera 3 CNAME records. Ejemplo:

```
Name:  abc123._domainkey.the-full-stack.com
Value: abc123.dkim.amazonses.com

Name:  def456._domainkey.the-full-stack.com
Value: def456.dkim.amazonses.com

Name:  ghi789._domainkey.the-full-stack.com
Value: ghi789.dkim.amazonses.com
```

### En Cloudflare DNS Dashboard

Para cada uno de los 3 CNAME records:

1. Click "+ Add Record"
2. Fill in:
   - Type: CNAME
   - Name: `abc123._domainkey` (el parte antes del dominio)
   - Content: `abc123.dkim.amazonses.com` (valor completo de AWS)
   - TTL: Auto
   - Proxy status: **DNS only** (CRITICO - NUNCA "Proxied")
3. Click "Save"

Repite para los otros 2 CNAME records.

**Espera**: Cloudflare propaga el cambio en minutos. SES verifica
automaticamente (puede tardar hasta 24h). En SES Console, el status de DKIM
cambia de "not verified" a "verified".

## Paso 3: Configurar SPF (1 TXT record)

SPF autoriza que servidores de mail pueden enviar email en nombre del dominio.

### En Cloudflare DNS

1. Click "+ Add Record"
2. Fill in:
   - Type: TXT
   - Name: `the-full-stack.com` (el apex, sin subdomain)
   - Content: `v=spf1 include:amazonses.com ~all`
   - TTL: Auto
   - Proxy status: DNS only
3. Click "Save"

**Explicacion**:
- `v=spf1`: Version 1 de SPF
- `include:amazonses.com`: Autoriza los mail servers de Amazon SES
- `~all`: Soft fail (emails NO autenticados tienen menos probabilidad de spam, pero no se rechazan)
  - Alternativa: `-all` (hard fail - rechaza emails no autenticados, mas estricto)

### Si ya existe SPF record

Si ya tienes un SPF record (de otro proveedor), AGREGAR `include:amazonses.com`:

**Antes**:
```
v=spf1 include:sendgrid.net ~all
```

**Despues**:
```
v=spf1 include:amazonses.com include:sendgrid.net ~all
```

## Paso 4: Configurar DMARC (1 TXT record)

DMARC define la politica de que hacer si un email FALLA SPF y DKIM.

### En Cloudflare DNS

1. Click "+ Add Record"
2. Fill in:
   - Type: TXT
   - Name: `_dmarc` (prefix)
   - Content: `v=DMARC1; p=quarantine; rua=mailto:pacg1991@gmail.com; ruf=mailto:pacg1991@gmail.com; fo=1`
   - TTL: Auto
   - Proxy status: DNS only
3. Click "Save"

**Explicacion**:
- `v=DMARC1`: Version de DMARC
- `p=quarantine`: Si DMARC falla, mandar el email a spam folder (no rechazar hard)
  - Alternativa: `p=none` (no hacer nada, solo reporte) — recomendado para testing
  - Alternativa: `p=reject` (rechazar directamente) — usa despues de probar
- `rua=mailto:pacg1991@gmail.com`: Reporte agregado (resumen diario)
- `ruf=mailto:pacg1991@gmail.com`: Reporte de forensica (emails fallidos)
- `fo=1`: Generar reporte si CUALQUIERA de SPF/DKIM falla

### DMARC workflow recomendado

**Fase 1 (Testing)**:
```
p=none; rua=mailto:pacg1991@gmail.com; ruf=mailto:pacg1991@gmail.com
```
→ No rechaza emails, solo reporta fallos. Esto te permite ver falsos positivos.

**Fase 2 (Produccion, despues de 1 semana)**:
```
p=quarantine; rua=mailto:pacg1991@gmail.com; ruf=mailto:pacg1991@gmail.com
```
→ Emails no autenticados van a spam. Mas seguro pero no rechaza hard.

**Fase 3 (Hardened, opcional)**:
```
p=reject; rua=mailto:pacg1991@gmail.com; ruf=mailto:pacg1991@gmail.com
```
→ Rechaza emails que fallan DMARC. Max seguridad, pero requiere SPF/DKIM
perfectos.

## Verificacion checklist

Despues de agregar todos los records:

- [ ] SES Console: DKIM status = "verified" (puede tardar 24h)
- [ ] SES Console: Domain verification = "verified"
- [ ] SPF valido: Verifica con [MXToolbox SPF Check](https://mxtoolbox.com/spf.aspx)
- [ ] DKIM valido: Verifica con [MXToolbox DKIM Check](https://mxtoolbox.com/dkim.aspx)
- [ ] DMARC valido: Verifica con [MXToolbox DMARC Check](https://mxtoolbox.com/dmarc.aspx)
- [ ] Enviar email de prueba desde SES
- [ ] Revisar email en Gmail/Outlook: debe tener "via" con dominio verificado

## Troubleshooting

### DKIM verification falla en SES console

**Problema**: SES dice "DKIM verification failed"

**Causas**:
1. Cloudflare "Proxy status" esta en "Proxied" (debe ser "DNS only")
2. El CNAME record value esta mal copiado
3. TTL no se propago aun (espera 30 minutos + reload)
4. Cloudflare tiene otro record CNAME conflictivo

**Solucion**:
1. Delete el CNAME record en Cloudflare
2. Copia el valor EXACTO de AWS (sin espacios extras)
3. Agregalo de nuevo con "DNS only"
4. Espera 5-10 minutos y retry "Verify" en SES

### SPF record value es muy largo

SPF puede tener max 10 includes. Si necesitas mas de 10:

```
v=spf1 include:_spf.google.com include:amazonses.com include:sendgrid.net ~all
```

Considera consolidar o usar un SPF router como [SPF/A record flattener](https://dmarcian.com/).

### DMARC reports no llegan a mi inbox

Si no recibes reportes:

1. DMARC record puede tener typo
2. Gmail puede estar bloqueando (DMARC reports vienen de `noreply` addresses)
3. Agregarlos a la whitelist en Gmail: Settings → Filters and Blocked Addresses

## Paso opcional: BIMI (Brand Indicators for Message Identification)

BIMI muestra tu logo en Gmail/Outlook. Requiere:
- DMARC policy = `p=quarantine` o `p=reject` (no `p=none`)
- SVG logo self-hosted
- BIMI record en DNS

Para este portfolio: **opcional** (no critico para 200 emails/mes).

## Timeline para el portfolio

```
Day 1:
  - Verifica dominio (TXT record)
  - Configura DKIM (3 CNAME records)

Day 2:
  - Verifica DKIM en SES (debe decir "verified")
  - Agrega SPF y DMARC

Day 3:
  - Verifica SPF/DMARC con MXToolbox
  - Test enviar email
  - Revisar en Gmail inbox vs spam
```

## Fuentes

- [AWS SES DKIM setup](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim.html)
- [AWS SES SPF](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-spf.html)
- [AWS SES DMARC](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html)
- [Cloudflare DNS setup guide](https://developers.cloudflare.com/dns/)
- [DMARC setup best practices](https://dmarcian.com/resources/dmarc-basics/)

**Verificado 2026-05-13**
