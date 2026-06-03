# 05 — Fase C: login.check-email (existencia + metodos disponibles)

[<- fase D](04-fase-d-fusion-login.md) | [Siguiente: fase A ->](06-fase-a-overview.md)

> Action liviana nueva `login.check-email`: dado un email (con Turnstile +
> rate-limit), devuelve si existe y que TIPOS de metodo de login tiene
> disponibles, SIN ningun dato sensible. Es lo que la UI consulta en el primer
> paso del login para mostrar "puedes usar estos metodos" o "crear cuenta".
> Cubre AC-C1..AC-C7. Rompe deliberadamente el anti-enumeration (decision 8).

## Por que va DESPUES de D

`check-email` reporta los metodos de un user; D ya consolido el flujo y eliminó
register. Hacer C sobre el login ya fusionado evita reportar metodos de un
concepto (register) que dejaria de existir.

## Contrato de la API

`POST /auth` body `{operation:'login', action:'check-email', email, cf_turnstile_response}`

Respuesta (200 en todos los casos no-error, para no filtrar por status code):

```jsonc
// existe, active, con metodos:
{ "is_valid": true, "code": 0, "data": {
  "exists": true,
  "pending": false,
  "methods": ["magic-link", "email-code", "password", "totp", "webauthn"]
}}
// no existe:
{ "is_valid": true, "code": 0, "data": {
  "exists": false, "methods": []
}}
// pending (debe terminar de verificar):
{ "is_valid": true, "code": 0, "data": {
  "exists": true, "pending": true,
  "methods": ["magic-link", "email-code"]
}}
// disabled/locked (existe, sin metodos):
{ "is_valid": true, "code": 0, "data": {
  "exists": true, "methods": [], "unavailable": true
}}
```

`methods` lista solo los TIPOS. NUNCA: el password hash, el TOTP secret, los
recovery codes, el `credential_id` de las passkeys, ni nada de otro user
(AC-C6). `magic-link` y `email-code` siempre estan disponibles para un user
verificado (son passwordless base); `password` solo si tiene credencial;
`totp`/`webauthn` solo si tiene esos metodos activos.

## 7.C Archivos afectados

### Crear — controller + modelo + service

- `core/controllers/login/check_email.py` — `CheckEmail(BaseController)`,
  `event_model=LoginCheckEmailIn`. `validate()` agrega Turnstile + rate-limit
  per-IP ANTES de tocar Neon (AC-C5). `execute()`:
  - Resuelve el user por email (lowercased).
  - None -> `{exists:false, methods:[]}`.
  - `pending` -> `{exists:true, pending:true, methods:['magic-link',
    'email-code']}`.
  - `disabled`/`locked`/`deleted` -> `{exists:true, methods:[], unavailable:true}`.
  - `active` -> arma `methods` consultando: siempre `magic-link`+`email-code`;
    `password` si `has_password`; `totp`/`webauthn` si tiene esos activos.
- `core/models/login.py` — `LoginCheckEmailIn {email: EmailStr,
  cf_turnstile_response: str|None, meta}`.
- `core/services/login_methods_service.py` (o reusar mfa/webauthn services) —
  `available_methods(*, user) -> list[str]` (consolida la consulta).
  - Verificar: tests de controller (exists/active, not-found, pending,
    disabled, sin-turnstile) [AC-C1..C7].

### Modificar — operations (sin cambio estructural)

- `core/settings/operations.py` — `login` ya registrada; el discovery toma
  `check_email.py` -> action `check-email`. Sin cambios.

### Anti-enumeration: actualizar la rule (se hace en fase E)

- `.claude/rules/auth-system.md` — la seccion "Login UX (anti enumeration)"
  cambia: `login.start`/`check-email` con email inexistente ya NO devuelve un
  404 indistinguible; ahora `check-email` reporta `exists:false` y `login.start`
  ofrece crear. Se documenta el trade-off y la mitigacion (rate-limit +
  Turnstile). disabled/locked SIGUEN sin revelar el estado real (solo
  `unavailable`).

## Mitigacion del riesgo de enumeracion

- **Turnstile obligatorio** en `check-email` (AC-C7): frena bots de enumeracion
  masiva.
- **Rate-limit per-IP estricto** (AC-C5): reusar la regla de `login.start` o una
  dedicada mas agresiva (ej. 10/min/IP). Se seedea en las reglas de rate-limit.
- **Auditoria**: `check-email` se audita (`event='login.check-email'`) para
  detectar patrones de enumeracion.
- El trade-off (exponer existencia) es una **decision consciente del dueño del
  producto**, documentada en la rule.

## Tests requeridos (Bloque C)

- `tests/unit/controllers/login/test_check_email_active_returns_methods.py`
  [AC-C1].
- `test_check_email_not_found.py` [AC-C2].
- `test_check_email_pending.py` [AC-C3].
- `test_check_email_disabled_unavailable.py` [AC-C4].
- `test_check_email_no_turnstile.py` [AC-C7].
- `test_check_email_no_sensitive_data.py` — asserta que la respuesta NO contiene
  hash/secret/credential_id [AC-C6].

[<- fase D](04-fase-d-fusion-login.md) | [Siguiente: fase A ->](06-fase-a-overview.md)
