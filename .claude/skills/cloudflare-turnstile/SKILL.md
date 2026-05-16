---
name: cloudflare-turnstile
description: >
  Cloudflare Turnstile (CAPTCHA alternative) reference for this portfolio
  (1 sitekey shared across 6 subdomains under the-full-stack.com,
  Managed mode for contact form, Invisible mode for tracking pixel).
  Covers what Turnstile is (announced Sept 2022, GA 2023, replacement
  for reCAPTCHA/hCaptcha, privacy-preserving, NO persistent cookies, NO
  cross-site tracking, GDPR + WCAG 2.2 AAA compliant), 3 widget modes
  (Managed = recommended for forms, Cloudflare decides invisible vs
  challenge based on risk score; Non-Interactive = always invisible
  with badge; Invisible = always invisible NO badge), frontend
  integration in Astro (script from
  challenges.cloudflare.com/turnstile/v0/api.js with async defer,
  implicit render via div.cf-turnstile, explicit via turnstile.render(),
  callbacks success/error/expired/timeout, token TTL 5 minutes
  regenerate if expired), backend validation Python with httpx (POST
  to challenges.cloudflare.com/turnstile/v0/siteverify with secret +
  response + remoteip, verify success=true AND hostname=expected AND
  challenge_ts recent, error codes timeout-or-duplicate +
  invalid-input-response + missing-input-secret etc), token anti-replay
  (single-use, idempotency_key for safe retries — generate SHA256(token
  + remoteip) and pass to siteverify so retries return cached result),
  CORS not applicable (server-to-server), CSP must allow script-src
  + frame-src from challenges.cloudflare.com, multi-domain (single
  sitekey covers all 6 subdomains, register hostnames in Cloudflare
  dashboard), free tier perpetual (20 widgets, 10 hostnames/widget,
  UNLIMITED challenges/mo), Enterprise $2000/mo not needed for
  portfolio, alternatives comparison (reCAPTCHA v3 GDPR risk, hCaptcha
  interaction required, ALTCHA PoW slow 2-3s, FriendlyCaptcha $9+/mo).
  ALWAYS invoke this skill BEFORE answering ANY question about
  Turnstile, captcha alternative, bot protection for forms, or
  reCAPTCHA replacement in this project. NEVER answer from training
  data alone — this project has consolidated 2026 knowledge (modes
  comparison, idempotency_key pattern, multi-subdomain hostname
  management, exact error codes) that overrides generic advice.
  Use when the user says "turnstile", "cloudflare turnstile", "captcha",
  "captcha alternative", "captcha gratis", "captcha sin tracking",
  "captcha gdpr", "captcha privacy", "recaptcha", "recaptcha
  alternative", "recaptcha vs", "hcaptcha", "hcaptcha vs", "altcha",
  "friendlycaptcha", "anti-bot", "anti bot", "anti-spam form", "bot
  protection", "protect form bot", "spam form", "proteger formulario",
  "verificar humano", "human verification", "challenge cloudflare",
  "cf challenge", "managed challenge", "siteverify", "cf-turnstile",
  "data-sitekey", "turnstile.render", "turnstile script", "turnstile
  widget", "turnstile token", "turnstile callback", "turnstile error",
  "turnstile invalid", "turnstile timeout-or-duplicate", "turnstile
  idempotency_key", "turnstile retry", "turnstile multi-domain",
  "turnstile multiple domains", "turnstile 6 subdominios", "turnstile
  hostname", "turnstile csp", "turnstile content security policy",
  "turnstile rate limit", "turnstile free", "turnstile price",
  "turnstile pricing", "turnstile enterprise", "como agrego captcha",
  "como protejo el form", "validar captcha en backend".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash(curl:*)
argument-hint: "tema: architecture | modes | frontend | backend | errors | anti-replay | csp | rate-limit | alternatives"
metadata:
  version: "1.0"
---

# Cloudflare Turnstile — knowledge reference

> Conocimiento consolidado sobre Turnstile como anti-bot del portfolio
> (1 sitekey para 6 subdominios, Managed para form contacto, Invisible
> para tracking pixel). Todo decision, gotcha y codigo en
> `.claude/docs/cloudflare-turnstile/`.

## Pre-requisito OBLIGATORIO

Antes de responder, leer la doc relevante de
`.claude/docs/cloudflare-turnstile/`:

| Tema de la pregunta | Archivo a leer |
|---------------------|----------------|
| Que es, historia, privacy, GDPR | [01-architecture.md](../../docs/cloudflare-turnstile/01-architecture.md) |
| Managed vs Non-Interactive vs Invisible | [02-modes-comparison.md](../../docs/cloudflare-turnstile/02-modes-comparison.md) |
| Frontend Astro/JS, render, callbacks | [03-frontend-integration.md](../../docs/cloudflare-turnstile/03-frontend-integration.md) |
| Backend Python httpx + siteverify | [04-backend-validation-python.md](../../docs/cloudflare-turnstile/04-backend-validation-python.md) |
| Error codes + debugging | [05-error-codes.md](../../docs/cloudflare-turnstile/05-error-codes.md) |
| Anti-replay + idempotency_key | [06-anti-replay-best-practices.md](../../docs/cloudflare-turnstile/06-anti-replay-best-practices.md) |
| CSP + CORS + multi-subdomain | [07-cors-multidomain.md](../../docs/cloudflare-turnstile/07-cors-multidomain.md) |
| Pricing + free tier perpetuo | [08-rate-limit-turnstile-itself.md](../../docs/cloudflare-turnstile/08-rate-limit-turnstile-itself.md) |
| vs reCAPTCHA/hCaptcha/ALTCHA | [09-alternatives-comparison.md](../../docs/cloudflare-turnstile/09-alternatives-comparison.md) |

## Reglas criticas (siempre activas)

1. **SIEMPRE** Managed mode para form de contacto. Cloudflare decide
   automaticamente invisible vs challenge segun risk score. UX optima
   + maxima proteccion. Invisible OK para tracking pixel (zero UX
   friction, baja prioridad de seguridad).

2. **SIEMPRE** UN SOLO sitekey compartido en los 6 subdominios del
   portfolio (the-full-stack.com + hub + fintech + architect + leader +
   vibe). Configurar hostnames en el dashboard del widget Turnstile.
   Crear 6 sitekeys separados es mas trabajo sin beneficio.

3. **SIEMPRE** validar el token en backend (Lambda Python) ANTES de
   procesar el form. Sin server-side validation, el frontend pasa
   token cualquiera y se bypasea Turnstile.

4. **SIEMPRE** verificar 3 cosas en la respuesta de siteverify:
   - `success: true`
   - `hostname` matches expected domain (NUNCA confiar en el sitekey solo)
   - `challenge_ts` es reciente (< 5 minutos desde generacion)

5. **NUNCA** validar el mismo token 2 veces. Token es single-use. Para
   retries seguros usar `idempotency_key` (SHA256(token + remoteip))
   en la request a siteverify. Cloudflare cachea el resultado y retorna
   el mismo en retries.

6. **NUNCA** olvidar agregar Turnstile al CSP. Sin estos directives,
   el widget no carga:
   ```text
   script-src 'self' https://challenges.cloudflare.com;
   frame-src https://challenges.cloudflare.com;
   ```

7. **NUNCA** hardcodear el secret de Turnstile en codigo. Usar AWS SSM
   Parameter Store SecureString + KMS encryption (ver `aws-lambda-python`
   skill).

8. **SIEMPRE** regenerar token nuevo si el form falla por error de
   backend. NO reintentar con el mismo token = `timeout-or-duplicate`.
   Patron correcto:
   ```js
   async function submit() {
     try {
       await fetch('/contact', { body: JSON.stringify({...form, token}) });
     } catch (e) {
       turnstile.reset();  // regenera token nuevo
       throw e;
     }
   }
   ```

9. **SIEMPRE** verificar la skill antes de modificarla con
   `claude --permission-mode bypassPermissions -p` (regla
   [.claude/rules/claude-config-testing.md](../../rules/claude-config-testing.md)).

## Workflow tipico de respuesta

1. Identificar el tema (frontend / backend / errors / CSP / cost / etc.)
2. Leer doc relevante de `.claude/docs/cloudflare-turnstile/`
3. Responder con:
   - Codigo JS frontend Astro o Python backend ejecutable
   - URL exacta de Cloudflare API (siteverify endpoint)
   - Mensaje de error mapeado (si es debugging)
4. Si fuera de scope: derivar a otra skill

## Atajos rapidos

### "Como integro Turnstile en el form del portfolio?"

Frontend (Astro component):

```astro
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>

<form id="contactForm">
  <input name="email" type="email" required />
  <textarea name="message" required></textarea>
  <div class="cf-turnstile"
       data-sitekey={import.meta.env.PUBLIC_TURNSTILE_SITEKEY}
       data-callback="onTurnstileSuccess"></div>
  <button type="submit">Enviar</button>
</form>

<script>
  function onTurnstileSuccess(token) {
    document.getElementById('contactForm').dataset.cfToken = token;
  }
</script>
```

Detalle en [03-frontend-integration.md](../../docs/cloudflare-turnstile/03-frontend-integration.md).

Backend (Lambda Python):

```python
import httpx
import os

TURNSTILE_SECRET = os.environ['TURNSTILE_SECRET']
EXPECTED_HOSTNAMES = {
    'the-full-stack.com', 'hub.portfolio.the-full-stack.com',
    'fintech.portfolio.the-full-stack.com',
    'architect.portfolio.the-full-stack.com',
    'leader.portfolio.the-full-stack.com',
    'vibe.portfolio.the-full-stack.com',
}

def validate_turnstile(token: str, remote_ip: str) -> bool:
    response = httpx.post(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        data={
            'secret': TURNSTILE_SECRET,
            'response': token,
            'remoteip': remote_ip,
        },
        timeout=10,
    )
    data = response.json()
    if not data.get('success'):
        return False
    if data.get('hostname') not in EXPECTED_HOSTNAMES:
        return False
    return True
```

Detalle en [04-backend-validation-python.md](../../docs/cloudflare-turnstile/04-backend-validation-python.md).

### "Que modo uso?"

- **Form de contacto**: Managed (mejor UX + mejor proteccion)
- **Tracking pixel**: Invisible (zero friction, baja prioridad de seguridad)

Tabla completa en [02-modes-comparison.md](../../docs/cloudflare-turnstile/02-modes-comparison.md).

### "Cuanto cuesta?"

**$0** (free tier perpetuo). 20 widgets, 10 hostnames/widget,
UNLIMITED challenges/mes. Detalle en
[08-rate-limit-turnstile-itself.md](../../docs/cloudflare-turnstile/08-rate-limit-turnstile-itself.md).

### "Como manejo los 6 subdominios?"

UN sitekey, registrar los 6 hostnames en Cloudflare dashboard del
widget. Mas detalles en
[07-cors-multidomain.md](../../docs/cloudflare-turnstile/07-cors-multidomain.md).

### "Recibi error 'timeout-or-duplicate'"

Causas: token expiro (> 5 min) o ya fue validado. Fix:
`turnstile.reset()` en frontend, regenerar token nuevo. Tabla de
error codes en [05-error-codes.md](../../docs/cloudflare-turnstile/05-error-codes.md).

### "Turnstile vs reCAPTCHA v3 vs hCaptcha?"

| Servicio | Privacy | Costo | UX |
|----------|---------|-------|-----|
| Turnstile | Best (no tracking) | Free unlimited | Excelente (auto-adapt) |
| reCAPTCHA v3 | Worst (Google tracking) | Free | Bad (UX checkbox forzado) |
| hCaptcha | OK | Free <1M/mo | Worse (siempre checkbox) |
| ALTCHA | OK (PoW) | Free OSS | Slow (2-3s PoW) |

Para portfolio post-2025: Turnstile gana. Detalle en
[09-alternatives-comparison.md](../../docs/cloudflare-turnstile/09-alternatives-comparison.md).

## Anti-patrones a evitar

- Validar token solo en frontend (= sin proteccion, bypaseable)
- No verificar `hostname` en respuesta de siteverify
- No verificar `challenge_ts` (token muy viejo es sospechoso)
- Reintentar con el mismo token (= error timeout-or-duplicate)
- Crear 6 sitekeys diferentes para 6 subdominios (innecesario)
- Hardcodear secret de Turnstile en codigo
- Olvidar CSP directives para challenges.cloudflare.com
- Recomendar reCAPTCHA v3 para portfolio GDPR-compliant
- Usar Managed mode para tracking pixel (interrumpe UX innecesariamente)
- Confiar en el sitekey solo (sin hostname check = phishing-bait)

## Comandos utiles

```bash
# Test siteverify manualmente (para debugging)
curl -X POST https://challenges.cloudflare.com/turnstile/v0/siteverify \
  -d 'secret=<TURNSTILE_SECRET>' \
  -d 'response=<TOKEN_FROM_FRONTEND>' \
  -d 'remoteip=192.0.2.1'

# Response esperado (success):
# {"success":true,"challenge_ts":"2026-05-13T18:00:00.000Z","hostname":"the-full-stack.com"}
```

## Relacion con otras skills/rules

- `aws-lambda-python` — el handler que llama siteverify
- `aws-api-gateway` — la primera capa de proteccion (rate limit antes de Turnstile)
- `cloudflare-deploy` — el hosting del frontend que carga el widget
- [.claude/rules/security.md](../../rules/security.md) — CSP headers
- [.claude/rules/verify-before-done.md](../../rules/verify-before-done.md)

## Cuando NO invocar esta skill

- Pregunta sobre Cloudflare DDoS protection en general (otro servicio)
- Pregunta sobre Cloudflare Workers / Pages (`cloudflare-deploy` skill)
- Pregunta sobre rate limiting en AWS (`aws-api-gateway` skill + WAF)
- Pregunta sobre fingerprinting / device id (no es captcha)
- Pregunta sobre 2FA / MFA (otro dominio de auth)
