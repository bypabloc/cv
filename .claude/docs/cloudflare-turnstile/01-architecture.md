# Arquitectura de Cloudflare Turnstile

> Que es Turnstile, por que fue creado, como funciona, historia y posicion
> en el mercado de CAPTCHA alternatives.

[← README](./README.md) | [Siguiente: Modos →](./02-modes-comparison.md)

## Que es Turnstile

Cloudflare Turnstile es una **alternativa privacy-preserving a CAPTCHA tradicional**
anunciada el **28 de septiembre de 2022** y lanzada en disponibilidad general
(GA) en **2023**. No requiere que el usuario resuelva puzzles visuales.

Turnstile usa "una suite rotativa de desafios no-intrusivos basados en
telemetria y comportamiento del cliente" — pruebas de proof-of-work,
proof-of-space, API probing — para determinar si el visitante es humano o bot.

## Historia del anuncio

En el blog de Cloudflare de Sept 2022, criticaron que Google reCAPTCHA domina
el 98% del mercado CAPTCHA mientras crea riesgos de privacidad (tracking
cross-site, data retention). Turnstile fue presentada como solucion que:

1. No requiere user interaction en la mayoria de casos (Managed mode)
2. Minimiza data collection (sin cookies persistentes)
3. Es gratuita para todos (no solo clientes Cloudflare)
4. Se integra sin enrutar trafico a traves de la CDN de Cloudflare

## Posicion en el mercado

| Solucion | Tracking | UX | Precio | GDPR |
|----------|----------|-----|--------|------|
| reCAPTCHA v3 | Alto (Google) | Bueno | Gratis | Risky |
| hCaptcha | Bajo | Requiere interaccion | Freemium | OK |
| Turnstile | Minimal | Excelente (invisible) | Gratis | Compliant |
| ALTCHA | Minimal | PoW, no visual | Paid | Compliant |
| FriendlyCaptcha | Minimal | PoW | Paid | Compliant |

**Turnstile ganador para este portfolio** por ser gratis, GDPR-friendly y
ofrecer mejor UX sin sacrificar seguridad.

## Como funciona internamente

### Cliente (navegador)

1. Script JS carga desde `https://challenges.cloudflare.com/turnstile/v0/api.js`
2. Widget Turnstile se renderiza (invisible o checkbox visible segun modo)
3. Se ejecutan "desafios pequenos no-intrusivos": computacion local,
   pruebas de APIs del browser, analisis de comportamiento
4. Si riesgo es BAJO (usuario legit): genera token automaticamente sin UI
5. Si riesgo es ALTO (bot): muestra checkbox o desafio interactivo
6. Token se expone a JS via callback `onTurnstileSuccess(token)`

### Servidor

1. Frontend envia token al backend (POST /contact, body form data)
2. Backend valida: POST a `https://challenges.cloudflare.com/turnstile/v0/siteverify`
3. Cloudflare verifica: secret + response token + remoteip (opcional)
4. Response: `{ success: bool, challenge_ts, hostname, error_codes[] }`
5. Backend verifica: success=true, hostname=expected, timestamp reciente (< 5min)
6. Si OK: procesa form; si NO: rechaza y regenara token en cliente

## Compliance y seguridad

- **WCAG 2.2 AAA compliant** — accesibilidad garantizada
- **No GDPR violation** — minimal data collection, sin cross-site tracking
- **EU AI Act compatible** — no classification como "high-risk AI"
- **Anti-replay** — cada token solo se valida UNA VEZ

## Cuando usar Turnstile

1. Forms de contacto (POST /contact)
2. Tracking pixels (invisible, confirma browser real)
3. Endpoints privados de APIs que necesitan user confirmation
4. Cualquier formulario publico que quiera evitar spam

**NO usar Turnstile** si:
- Tu app requiere autenticacion (usa JWT/OAuth en su lugar)
- La mayoria de usuarios estan en paises donde Cloudflare esta bloqueado
- Necesitas full offline validation (Turnstile requiere HTTP a Cloudflare)
