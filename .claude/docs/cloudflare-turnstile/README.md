# Cloudflare Turnstile integration guide

> Conocimiento consolidado sobre integracion de Cloudflare Turnstile
> (CAPTCHA alternative privacy-preserving) en el portfolio de Pablo Contreras.
> Protege form de contacto y tracking pixel contra bots. Cada nodo cubre un
> tema; navegar por relevancia, no leer linealmente.

## Cuando leer cada archivo

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Que es Turnstile, historia, arquitectura | [01-architecture.md](./01-architecture.md) | Entender por que Turnstile vs reCAPTCHA/hCaptcha; anuncio Sept 2022, GA 2023 |
| Modos: Managed vs Non-Interactive vs Invisible | [02-modes-comparison.md](./02-modes-comparison.md) | Elegir que modo usar segun caso de uso (form de contacto vs tracking pixel) |
| Implementacion widget en Astro/JS | [03-frontend-integration.md](./03-frontend-integration.md) | Cargar script, renderizar widget, callbacks, token TTL, regeneracion |
| Validacion token en Python (Lambda) | [04-backend-validation-python.md](./04-backend-validation-python.md) | POST a siteverify, verificar success + hostname + challenge_ts, codigo completo |
| Error codes del backend | [05-error-codes.md](./05-error-codes.md) | Significado de missing-input-secret, invalid-input-response, timeout-or-duplicate, etc. |
| Anti-replay + idempotency | [06-anti-replay-best-practices.md](./06-anti-replay-best-practices.md) | Token solo se valida UNA VEZ; patreon retry con idempotency_key |
| CSP y CORS multi-subdominio | [07-cors-multidomain.md](./07-cors-multidomain.md) | Directivas CSP (script-src, frame-src), sitekey compartido para 6 subdominios |
| Rate limits y free tier | [08-rate-limit-turnstile-itself.md](./08-rate-limit-turnstile-itself.md) | Free: 20 widgets, 10 hostnames/widget, unlimited challenges; sin rate limit por request |
| Alternativas: reCAPTCHA, hCaptcha, ALTCHA, etc. | [09-alternatives-comparison.md](./09-alternatives-comparison.md) | Por que Turnstile es correcta para este portfolio; GDPR/EU AI Act compliance |
| Verificacion 2026 | [VERIFICACION.md](./VERIFICACION.md) | Metadata de investigacion; fuentes; fecha de actualizacion |

## Reglas criticas

- NUNCA exponer secret key en frontend (solo sitekey)
- SIEMPRE validar token en backend (Python + httpx)
- Configurar CSP para permitir `https://challenges.cloudflare.com` en script-src y frame-src
- Usar Managed mode para form (mejor UX + protection)
- Usar Invisible para tracking pixel
- Agregar TODOS los 6 subdominios en hostname management del dashboard

## Quick start: integrar form de contacto

```
1. Crear widget en Cloudflare dashboard (sitekey + secret)
2. Agregar hostnames: the-full-stack.com + 5 subdominios
3. Cargar script JS en Astro: <script async defer src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>
4. Renderizar widget: <div class="cf-turnstile" data-sitekey="..." data-callback="onSuccess"></div>
5. Backend Python: POST a https://challenges.cloudflare.com/turnstile/v0/siteverify con secret + response
6. Verificar success=true, hostname correcto, timestamp reciente
7. Procesar form si validacion OK
```

## Estado actual (Verificacion 2026-05-13)

- Investigacion: Turnstile anunciado Sept 2022, GA 2023, Managed Challenge platform
- Modo recomendado: Managed para form (auto-detecta bots), Invisible para tracking
- Free tier: 20 widgets, 10 hostnames, unlimited challenges
- Privacy: GDPR/EU AI Act compliant, sin tracking cookies
- Alternativas: reCAPTCHA v3 (Google tracking), hCaptcha (privacy pero interactiva), ALTCHA (PoW)
