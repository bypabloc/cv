# SPEC-011: SES domain verification (DKIM/SPF/DMARC) + production access

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: AWS SES (us-west-2), Cloudflare DNS, ticket de
production access
**Dependencias**: SPEC-000
**Paralelizable con**: TODAS las otras specs (DNS setup no bloquea
desarrollo, solo el deploy final del email)

## 1. Contexto

Para que SES envie emails sin caer en spam, el dominio
`the-full-stack.com` necesita:
1. DKIM verificado (3 CNAMEs en Cloudflare DNS)
2. SPF record (1 TXT)
3. DMARC record (1 TXT con p=quarantine o p=reject)
4. Production access aprobado por AWS (24-48h espera)

Ademas durante sandbox, solo se puede enviar a addresses verificadas
(util para testing pero limitante en prod).

### Hallazgos de exploracion

- Skill `/aws-ses` documenta proceso completo en
  `.claude/docs/aws-ses/03-domain-verification-dns.md`
- Cloudflare DNS proxy DEBE estar OFF para CNAMEs DKIM (DNS only)
- Production access ticket tiene plantilla en
  `serverless/scripts/request_ses_production.md`

## 2. Solucion propuesta

### Pasos manuales (en orden)

1. **Domain identity en SES**:
   - AWS Console > SES > Verified identities > Create identity
   - Type: Domain
   - Domain: `the-full-stack.com`
   - Use a custom MAIL FROM domain: NO (skip para MVP)
   - DKIM signing: Easy DKIM (AWS genera 3 CNAMEs)
   - Anotar los 3 CNAMEs token._domainkey.the-full-stack.com -> ...amazonses.com

2. **Cloudflare DNS** (proxy OFF, DNS only en cada record):
   - 3x CNAME records DKIM (cada uno con proxy OFF)
   - 1x TXT SPF: `v=spf1 include:amazonses.com -all`
   - 1x TXT en `_dmarc.the-full-stack.com`:
     `v=DMARC1; p=quarantine; rua=mailto:dmarc@the-full-stack.com`
     (cambiar a `p=reject` despues de 30d sin reportes)

3. **Verificar DNS propagation**:
   ```bash
   serverless verify-ses-dns
   # Espera ~5-30 min para propagacion
   ```

4. **Esperar SES DKIM verification**:
   - Status en consola SES tarda hasta 24h en pasar a "Verified"
   - Puede llegar antes (typical 15min - 2h)

5. **Solicitar production access**:
   - AWS Console > SES > Account dashboard > Request production access
   - Llenar formulario con plantilla de
     `serverless/scripts/request_ses_production.md`
   - Espera 24-48h para aprobacion

6. **Configurar account-level Suppression** (cuando production access aprobado):
   - SES > Suppression list > Enable account-level suppression
   - Auto-maneja bounces + complaints sin reenviar a esos addresses

### Decisiones clave

- **Decision 1: DMARC `p=quarantine` inicial** — vs `p=reject`. Razon:
  primer mes recibimos reportes DMARC para detectar misconfiguracion
  antes de bloquear emails legitimos.
- **Decision 2: Sin BIMI en MVP** — el record BIMI muestra logo en
  Gmail/Outlook. Requiere certificado VMC ($1500/ano), overkill para
  portfolio personal.
- **Decision 3: No custom MAIL FROM domain** — `bounces@`. Skip
  porque agrega 2 records DNS adicionales sin beneficio para
  bajo volumen.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given los 3 CNAMEs DKIM agregados a Cloudflare con proxy OFF,
  When ejecuto `dig +short CNAME <token>._domainkey.the-full-stack.com`,
  Then retorna `<token>.dkim.amazonses.com`
- **AC-2**: Given TXT SPF agregado, When ejecuto
  `dig +short TXT the-full-stack.com`, Then incluye
  `v=spf1 include:amazonses.com -all`
- **AC-3**: Given TXT DMARC agregado, When ejecuto
  `dig +short TXT _dmarc.the-full-stack.com`, Then incluye
  `v=DMARC1; p=quarantine`
- **AC-4**: Given DKIM propagado, When inspecciono SES Console >
  Verified identities > the-full-stack.com, Then status =
  "Identity status: Verified" y "DKIM status: Successful"
- **AC-5**: Given production access aprobado, When inspecciono
  SES > Account dashboard, Then "Sending account status: Healthy" y
  "Production access: Enabled"
- **AC-6**: Given todo verificado, When envio email de prueba via
  `aws sesv2 send-email --from no-reply@the-full-stack.com --to
  pacg1991@gmail.com ...`, Then email llega a inbox de Gmail (NO spam)
  con score Mail Tester >= 8/10
- **AC-7**: Given account-level Suppression habilitado, When inspecciono
  SES > Suppression list, Then status = "Enabled"

## 4. Diagrama de Flujo

N/A — setup manual.

## 5. Diagrama ER

N/A.

## 6. Tests Requeridos

### 6.E. Manual verification

```bash
# 1. Verificar DNS propagation
dig +short CNAME <dkim-token-1>._domainkey.the-full-stack.com
dig +short CNAME <dkim-token-2>._domainkey.the-full-stack.com
dig +short CNAME <dkim-token-3>._domainkey.the-full-stack.com
dig +short TXT the-full-stack.com | grep spf1
dig +short TXT _dmarc.the-full-stack.com

# Helper que verifica todo
serverless verify-ses-dns

# 2. Verificar SES status
aws sesv2 get-email-identity \
  --email-identity the-full-stack.com \
  --region us-west-2

# 3. Smoke test send (sandbox o post-prod)
aws sesv2 send-email \
  --from-email-address no-reply@the-full-stack.com \
  --destination 'ToAddresses=pacg1991@gmail.com' \
  --content '{"Simple":{"Subject":{"Data":"Test SES"},"Body":{"Text":{"Data":"Hola desde SES"}}}}' \
  --region us-west-2

# 4. Mail Tester
# Enviar a test-XXX@mail-tester.com (genera URL temporal)
# Verificar score >= 8/10
```

## 7. Archivos Afectados

### Crear

- `serverless/scripts/request_ses_production.md` — plantilla del ticket
  (generado por `serverless request-ses-prod`)
- `serverless/docs/ses-setup.md` — guia de ops con DNS records exactos
  + screenshots referencia + troubleshooting

### Modificar

- `serverless/docs/secrets.md` — agregar referencia a SES domain identity
  + Suppression list

### Configuraciones externas (no archivos)

- AWS SES Console (us-west-2)
- Cloudflare DNS dashboard
- AWS SES production access ticket (formulario web)

## 8. Descomposicion para Paralelizacion

N/A — Small spec, secuencial por naturaleza.

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-000 done (KMS + SSM base)
- [ ] Cuenta Cloudflare con acceso a DNS de the-full-stack.com
- [ ] AWS Console acceso para SES y para Support Center (production
      access ticket)

### Definition of Done

- [ ] AC-1 a AC-7 cumplidos
- [ ] Email de prueba llega a Gmail inbox sin tocar spam
- [ ] Mail Tester score >= 8/10
- [ ] SES Reputation Dashboard verde (no warnings)
- [ ] Account-level Suppression habilitado
- [ ] `serverless verify-ses-dns` retorna OK
- [ ] Documentacion actualizada con DKIM tokens reales (gitignored,
      solo en `serverless/env/.env.dev` local)
