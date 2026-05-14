# CSP, CORS y multi-subdominio

> Como configurar Content Security Policy para Turnstile,
> y usar un solo sitekey para los 6 subdominios del portfolio.

[← Anti-replay](./06-anti-replay-best-practices.md) | [Siguiente: Rate limits →](./08-rate-limit-turnstile-itself.md)

## CORS (no aplica a Turnstile)

Turnstile NO tiene problema de CORS porque:

- El endpoint siteverify es **server-to-server** (Lambda → Cloudflare)
  — No cruza browsers, no hay preflight
- El widget JS client-side carga desde `challenges.cloudflare.com`
  — Es un CDN publico, permite cross-origin

## Content Security Policy (CSP) — CRITICAL

Si tu portfolio usa CSP strict, **DEBES agregar estas directivas**:

### CSP minimo para Turnstile

```
script-src 'self' https://challenges.cloudflare.com;
frame-src https://challenges.cloudflare.com;
```

### CSP completo recomendado (Astro portfolio)

```
default-src 'self';
script-src 'self' https://challenges.cloudflare.com;
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self';
frame-src https://challenges.cloudflare.com;
connect-src 'self' https://challenges.cloudflare.com https://api.* ;
object-src 'none';
base-uri 'self';
form-action 'self';
```

### Headers file (Cloudflare Pages)

En `apps/*/public/_headers`:

```
/*
  Content-Security-Policy: script-src 'self' https://challenges.cloudflare.com; frame-src https://challenges.cloudflare.com; default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; font-src 'self'; connect-src 'self' https://challenges.cloudflare.com; object-src 'none'
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
```

## Multi-subdominio: OPCION 1 (RECOMENDADO)

Un sitekey para TODOS los 6 subdominios.

### Paso 1: Crear widget en dashboard Cloudflare

1. Ir a `https://dash.cloudflare.com/` → Turnstile
2. Click "Create site"
3. Name: "portfolio-generic" (o similar)
4. Domain: Agregar todos los 6 subdominios

```
the-full-stack.com
hub.the-full-stack.com
fintech.the-full-stack.com
architect.the-full-stack.com
leader.the-full-stack.com
vibe.the-full-stack.com
```

4. Mode: "Managed" para form de contacto
5. Click Create
6. Copiar **sitekey** y **secret key**

### Paso 2: Guardar en variables de entorno

```bash
# .env.production (local, no committear)
PUBLIC_TURNSTILE_SITEKEY=1x00000000000000000000AA
TURNSTILE_SECRET_KEY=1x0000000000000000000000000000000AAA
```

Turnstile **sitekey** DEBE ser `PUBLIC_*` (se expone en HTML).
**Secret key** NUNCA se expone.

### Paso 3: Usar en Astro

En cualquiera de los 6 apps:

```astro
---
// src/components/ContactForm.astro
const sitekey = import.meta.env.PUBLIC_TURNSTILE_SITEKEY
---

<div
  class="cf-turnstile"
  data-sitekey={sitekey}
  data-theme="managed"
  data-callback="onTurnstileSuccess"
></div>
```

El widget funcionara identicamente en los 6 subdominios con el mismo sitekey.

### Paso 4: Backend (Lambda) valida hostname

En `04-backend-validation-python.md`, verificamos que `hostname` en la
respuesta siteverify sea uno de los 6 subdominios:

```python
ALLOWED_HOSTNAMES = {
    "the-full-stack.com",
    "hub.the-full-stack.com",
    "fintech.the-full-stack.com",
    "architect.the-full-stack.com",
    "leader.the-full-stack.com",
    "vibe.the-full-stack.com",
}

def validate_turnstile_token(token: str, remote_ip: str) -> dict:
    result = siteverify(token, remote_ip)

    if result["hostname"] not in ALLOWED_HOSTNAMES:
        raise TurnstileValidationError(
            f"Invalid hostname: {result['hostname']}",
            error_code="invalid_hostname",
        )

    return result
```

## Multi-subdominio: OPCION 2 (NO RECOMENDADO)

Crear **6 widgets diferentes**, uno por app.

### Ventajas

- Separacion logica (cada app su key)
- Stats de Turnstile separadas

### Desventajas

- **MUCHO MAS TRABAJO** — 6 pares sitekey/secret
- Duplicar codigo Astro en 6 componentes
- Harder to rotate keys (6 cambios en lugar de 1)

**Veredicto:** No hagas esto. Usa Opcion 1.

## Troubleshooting CSP

### Problema: Widget carga pero hay warning en console

```
Refused to load the script 'https://challenges.cloudflare.com/turnstile/v0/api.js'
because it violates the following Content Security Policy directive...
```

**Solucion:** Agregar `https://challenges.cloudflare.com` a `script-src`:

```
script-src 'self' https://challenges.cloudflare.com
```

### Problema: Widget aparece pero no funciona

```
Refused to frame 'https://challenges.cloudflare.com/...'
because it violates the following Content Security Policy directive...
```

**Solucion:** Agregar `https://challenges.cloudflare.com` a `frame-src`:

```
frame-src https://challenges.cloudflare.com
```

### Problema: No puedo usar nonce en CSP con Turnstile

**Recomendacion de Cloudflare:** Si usas CSP3 con nonce, incluir el nonce
en el script tag del Turnstile API:

```astro
<script
  async
  defer
  src="https://challenges.cloudflare.com/turnstile/v0/api.js"
  nonce="random-nonce-value"
></script>
```

Turnstile propagara el nonce a sus iframes dinamicos internos.

## Hostname management: Verificacion

Luego de crear el widget en dashboard, verificar que todos los 6
hostnames estan configurados:

```bash
# Listar widgets via API
curl -X GET "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/challenges/widgets" \
  -H "Authorization: Bearer <API_TOKEN>" | jq '.result[] | {id, name, domains}'
```

Output esperado:

```json
{
  "id": "...",
  "name": "portfolio-generic",
  "domains": [
    "the-full-stack.com",
    "hub.the-full-stack.com",
    "fintech.the-full-stack.com",
    "architect.the-full-stack.com",
    "leader.the-full-stack.com",
    "vibe.the-full-stack.com"
  ]
}
```

Si faltan algunos, editarlos en dashboard o via API PUT.

## Anti-patterns

- ❌ Hardcodear sitekey en codigo (no en env)
- ❌ Usar diferentes sitekeys en diferentes apps (OPCION 2)
- ❌ No verificar hostname en backend (permite token de otro dominio)
- ❌ Olvidar frame-src en CSP
