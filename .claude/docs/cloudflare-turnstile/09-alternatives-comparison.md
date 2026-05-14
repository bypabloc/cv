# Comparacion de alternativas: por que Turnstile gana

> Evaluacion de Turnstile vs reCAPTCHA, hCaptcha, ALTCHA, y otras
> alternativas. Juicio final: Turnstile es la opcion correcta.

[← Rate limits](./08-rate-limit-turnstile-itself.md) | [Siguiente: Verificacion →](./VERIFICACION.md)

## Comparacion cuantitativa

| Criterio | Turnstile | reCAPTCHA v3 | hCaptcha | ALTCHA | FriendlyCaptcha |
|----------|-----------|-------------|----------|--------|-----------------|
| **Precio** | Gratis | Gratis (pero Google tracking) | Freemium | Freemium | Paid ($9+/mes) |
| **UX (no captcha)** | Excelente (95%) | Bueno (invisible) | Intermedia (checkbox) | Intermedia (PoW) | Intermedia (PoW) |
| **Privacy** | GDPR OK | Risky (Google) | OK (pero ML training) | Excelente | Excelente |
| **Setup** | Facil (5 min) | Facil (5 min) | Facil (5 min) | Intermedia | Intermedia |
| **Requiere CDN** | NO | NO | NO | NO | NO |
| **Open source** | NO | NO | NO | SI (ALTCHA) | SI (partial) |
| **Rate limit** | Ilimitado | Ilimitado | ~1000/mes free | Ilimitado | Depende plan |

## Google reCAPTCHA v3

### Ventajas

- Muy efectivo contra bots
- Compatible con accesibilidad
- Precio "gratis" (pero...)

### Desventajas

- **Google tracking:** Crea risk GDPR/privacidad. reCAPTCHA colecta
  comportamiento, referrer, User-Agent para profile de usuario
- **Requiere consentimiento GDPR explícito** en muchas jurisdicciones
  (overhead legal, aviso, cookie banner)
- **Menos transparent:** Google no documenta exactamente que señales usa
- **Domina 98% del mercado:** Si todos lo usan, los bots lo optimizan mejor

### Verdict para este portfolio

NO recomendado. Es gratis en precio pero caro en privacidad.

## hCaptcha

### Ventajas

- Privacy-first (no cross-site tracking)
- Alternativa "bonita" a Google
- WCAG 2.2 AAA compliant

### Desventajas

- **Requiere interaccion** (checkbox, a veces puzzle)
  — Mala UX comparada a Turnstile invisible
- **Basada en image-labeling:** Si usa dataset de ML, tu form data
  entrena sus modelos (algo invasivo)
- **Freemium:** 1000 verificaciones/mes free, luego $3+/mes
- **Menos popular:** Menos visto en bots, pero tambien menos tested
  contra ataques nuevos

### Verdict para este portfolio

Aceptable pero inferior a Turnstile. La interaccion requirida (checkbox)
es friccion que Turnstile evita.

## ALTCHA (Open Source)

### Ventajas

- **Open source:** Puedes auto-hostear
- **Privacy-first:** PoW (proof-of-work), sin servidor, sin tracking
- **Sin overhead legal:** No requiere consentimiento GDPR
- **Accessibility:** WCAG AAA compliant

### Desventajas

- **Basada en PoW:** Cliente hace computacion pesada (2-3 segundos)
  — peor UX que Turnstile
- **Less tested against modern bots:** Smaller community, menos academic study
- **Freemium:** Gratuita para self-host, pero SaaS es freemium

### Verdict para este portfolio

Es una opcion solida, pero PoW es mas molesto que Turnstile Managed.
Si Cloudflare desaparece, ALTCHA es fallback razonable.

## FriendlyCaptcha

### Ventajas

- **Proof-of-work friendly UX:** Mejor que ALTCHA
- **Privacy:** GDPR compliant, sin tracking
- **Accessible:** WCAG AAA
- **European-based:** GDPR compliance nativo

### Desventajas

- **Requiere pago:** $9+/mes (caro para portfolio)
- **PoW:** ~1s computacion (mas lento que Turnstile invisible)
- **Smaller community:** Menos audits, menos data en efectividad real

### Verdict para este portfolio

Demasiado caro para usar ($9/mes = $108/ano). No justificado.

## Matriz de decision para este portfolio

```
Requerimientos:
  - Gratis o muy barato ✓
  - Zero UX friction ✓
  - GDPR/privacy compliant ✓
  - No requiere mi CDN ✓
  - Efectivo contra bots ✓
  - Setup simple ✓

Candidatos que pasan todos:
  - Turnstile ✅ 6/6
  - ALTCHA ✅ 6/6 (pero PoW es friccion)
  - Otros: No pasan algun criterio
```

## Recommendation final: TURNSTILE

Razon: **Mejor balance de precio, UX y privacy.**

- **Gratis:** Sin costo indefinido (free tier estable)
- **Mejor UX:** 95% usuarios no ven nada (Managed mode)
- **GDPR OK:** Privacy-preserving, sin tracking persistent
- **Setup facil:** 5 minutos, 1 sitekey para 6 subdominios
- **Efectivo:** Adaptive risk assessment, mejor que fixed PoW
- **Fallback:** Si Cloudflare falla, migrar a ALTCHA en <1 hora

## EU AI Act / Compliance

La nueva regulacion EU AI Act (2024) no clasifica CAPTCHA como "high-risk AI".
Tanto Turnstile como sus alternativas estan OK desde perspectiva legal.

Ventajas de Turnstile:

- Cloudflare (company) con acta de compliance fuerte
- Documentation clara de datos procesados
- No hidden ML training (a diferencia de hCaptcha/reCAPTCHA)

## Migracion futura (si es necesario)

Si en algun momento quieres cambiar:

```
Turnstile → ALTCHA: ~1 hora (reemplazar JS, crear login en ALTCHA)
Turnstile → FriendlyCaptcha: ~1 hora (mismo)
Turnstile → reCAPTCHA: ~1 hora (mismo, pero GDPR prep)
```

Codigo backend (siteverify) es el 80% del trabajo. Frontend widget
es interchangeable (todos usan patron similar).

## Especificaciones recomendadas finales

Para este portfolio (2026-05-13):

- **Plataforma:** Cloudflare Turnstile
- **Plan:** Free (20 widgets, 10 hostnames, unlimited challenges)
- **Modo:** Managed (form de contacto), Invisible (tracking pixel)
- **Sitekey:** 1 compartido en 6 subdominios
- **Hostnames:** 6 registrados en dashboard
- **Backend validation:** Python httpx a siteverify
- **Idempotency:** Via SHA256(token + remoteip)
- **CSP:** script-src + frame-src para challenges.cloudflare.com
- **Monitoring:** CloudWatch metrics para internal-error
- **Fallback:** Manual migration a ALTCHA si necesario (<1 hora)
