# Verificacion de investigacion

> Metadata de la investigacion realizada. Fuentes, fecha, alcance.

**Fecha de investigacion:** 2026-05-13

**Investigador:** researcher (Claude Haiku 4.5)

**Estatus:** Completo

## Alcance investigado

- ✅ Arquitectura de Turnstile (que es, historia, anuncio Sept 2022, GA 2023)
- ✅ Modos de widget (Managed vs Non-Interactive vs Invisible)
- ✅ Implementacion frontend (Astro/JavaScript, renderizado, callbacks)
- ✅ Validacion backend (Python httpx, siteverify API endpoint)
- ✅ Error codes (mapping a HTTP status, debugging, logging)
- ✅ Anti-replay y idempotency (token single-use, idempotency_key)
- ✅ CSP y CORS (multi-subdominio, hostname management)
- ✅ Rate limits y free tier (pricing, limites, monitoring)
- ✅ Alternativas (reCAPTCHA, hCaptcha, ALTCHA, FriendlyCaptcha)
- ✅ Comparacion cuantitativa y juicio final

## Fuentes primarias (2025-2026)

| Fuente | URL | Acceso |
|--------|-----|--------|
| Cloudflare Turnstile Docs (official) | https://developers.cloudflare.com/turnstile/ | WebFetch OK |
| Turnstile announcement (Sept 2022) | https://blog.cloudflare.com/turnstile-private-captcha-alternative/ | WebFetch OK |
| Widget configuration | https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/widget-configurations/ | WebFetch OK |
| Server-side validation | https://developers.cloudflare.com/turnstile/get-started/server-side-validation/ | WebFetch OK |
| CSP requirements | https://developers.cloudflare.com/turnstile/reference/content-security-policy/ | WebFetch OK |
| Hostname management | https://developers.cloudflare.com/turnstile/additional-configuration/hostname-management/ | WebFetch OK |
| Plans and pricing | https://developers.cloudflare.com/turnstile/plans/ | WebFetch OK |

## Fuentes secundarias (comparativas 2026)

- [Top Cloudflare Turnstile Alternatives in 2026](https://friendlycaptcha.com/insights/cloudflare-captcha-alternative/) — FriendlyCaptcha
- [5 Best reCAPTCHA Alternatives](https://capmonster.cloud/en/blog/5-best-recaptcha-alternatives-in-2026-incl-cloudflare-turnstile)
- [Turnstile vs reCAPTCHA 8 Key Factors](https://www.geetest.com/en/article/cloudflare-turnstile-vs-google-recaptcha-8-key-factors)
- [ALTCHA - Open Source CAPTCHA](https://altcha.org/open-source-captcha/)

## Información verificada

| Hecho | Fuente | Confianza |
|-------|--------|-----------|
| Anuncio Sept 28, 2022 | Blog oficial Cloudflare | Alta |
| GA en 2023 | Blog oficial | Alta |
| Free plan: 20 widgets | developers.cloudflare.com | Alta |
| Free plan: 10 hostnames | developers.cloudflare.com | Alta |
| Challenges ilimitados | developers.cloudflare.com | Alta |
| Token TTL: 5 minutos | developers.cloudflare.com | Alta |
| Anti-replay: single-use | developers.cloudflare.com | Alta |
| idempotency_key soportado | developers.cloudflare.com | Alta |
| GDPR compliant | developers.cloudflare.com | Media-Alta |
| reCAPTCHA domina 98% | Anuncio Cloudflare | Media |
| ALTCHA is open source | altcha.org | Alta |
| FriendlyCaptcha: $9+/mes | friendlycaptcha.com | Alta |

## Gaps / Limitaciones

- **Undocumented:** Rate limit exacto de siteverify (estimado ~1000/min)
- **No tested:** Comportamiento bajo ataque DDoS masivo
- **Asumido:** EU AI Act compliance (no hay doc oficial)
- **Community-based:** Error codes del siteverify (no en docs oficiales, encontrados en foros)

## Recomendaciones por usar Turnstile

### Para este portfolio (2026-05-13)

1. **Plan:** Free (bastante para 15k validaciones/mes)
2. **Widget:** Managed para form, Invisible para tracking
3. **Setup:** 1 sitekey compartido en 6 subdominios
4. **Backend:** Python httpx + idempotency_key
5. **Monitoring:** CloudWatch metrics para errors
6. **Fallback:** ALTCHA si Cloudflare falla

### Pasos de implementacion

1. Crear widget en Cloudflare dashboard (5 min)
2. Registrar 6 subdominios en hostname management (5 min)
3. Copiar sitekey a .env (PUBLIC_TURNSTILE_SITEKEY)
4. Cargar script en Astro BaseLayout (async defer)
5. Renderizar widget en componente ContactForm
6. Implementar Lambda handler con siteverify validation + idempotency
7. Configurar CSP en _headers
8. Test en los 6 subdominios
9. Monitor metrics en CloudWatch

**Tiempo total:** ~4 horas de work

## Proximos pasos

Documentacion completa lista en:
```
.claude/docs/cloudflare-turnstile/
├── README.md
├── 01-architecture.md
├── 02-modes-comparison.md
├── 03-frontend-integration.md
├── 04-backend-validation-python.md
├── 05-error-codes.md
├── 06-anti-replay-best-practices.md
├── 07-cors-multidomain.md
├── 08-rate-limit-turnstile-itself.md
└── 09-alternatives-comparison.md
```

## Control de calidad

- ✅ Verificacion contra fuentes oficiales
- ✅ Codigo Python listo para copy-paste
- ✅ Ejemplos Astro completos
- ✅ Error codes mapeados
- ✅ Comparativas cuantitativas
- ✅ Recomendacion justificada
- ✅ Anti-patterns listados
- ✅ Checklist pre-deploy

## Metadata

| Campo | Valor |
|-------|-------|
| Status | Completo |
| Quality | Listo para produccion |
| Audience | Dev implementando Turnstile |
| Language | Espanol (terminos tecn. en ingles) |
| Idiom | Professional, technical |
| Length | ~450 lineas / 10 archivos |
| Verificacion | 2026-05-13 OK |
