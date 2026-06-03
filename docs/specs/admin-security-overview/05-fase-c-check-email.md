# 05 — Fase C: login.check-email (gated por password)

[<- fase D](04-fase-d-fusion-login.md) | [Siguiente: fase A ->](06-fase-a-overview.md)

> Action liviana nueva `login.check-email`: dado un email (con Turnstile +
> rate-limit), devuelve si existe y si tiene PASSWORD configurado — pero NO la
> lista de metodos MFA. La lista completa de metodos requeridos se revela solo
> DESPUES de verificar un factor (la password, o el magic-link/code passwordless).
> Asi la existencia (ya enumerable hoy) se expone, pero el reconnaissance de
> "que 2FA usa cada cuenta" queda detras de autenticacion. Cubre AC-C1..AC-C8.

## Decision de diseño: gated por password (el dato sensible detras de un factor)

La existencia de un email YA es enumerable hoy (`register.start` 409 vs
`login.start` 404). Exponerla en `check-email` no agrega riesgo real. Lo
NUEVO y sensible seria exponer la LISTA de metodos MFA (reconnaissance: revela
que 2FA usa cada cuenta). Solucion elegida:

- `check-email` expone: `exists`, `has_password`, `pending`/`unavailable`.
- `check-email` NO expone: la lista de metodos MFA ni nada sensible.
- **Si `has_password`**: la UI pide la password; tras `verify-password` OK, el
  backend revela `required_methods`/`methods` para el step-up (multi-factor de
  la fase B). El reconnaissance queda detras de la password.
- **Si NO `has_password`**: flujo passwordless directo (magic-link + code); los
  metodos extra (si hubiera) aparecen en el step-up tras el primer factor.

## Contrato de la API

`POST /auth` body `{operation:'login', action:'check-email', email, cf_turnstile_response}`

Respuesta (200 en casos no-error, para no filtrar por status code):

```jsonc
// existe, active, CON password -> la UI pedira la password:
{ "is_valid": true, "code": 0, "data": {
  "exists": true, "has_password": true
}}
// existe, active, SIN password -> flujo passwordless:
{ "is_valid": true, "code": 0, "data": {
  "exists": true, "has_password": false
}}
// no existe -> la UI ofrece crear cuenta:
{ "is_valid": true, "code": 0, "data": {
  "exists": false
}}
// pending (debe terminar de verificar) -> passwordless:
{ "is_valid": true, "code": 0, "data": {
  "exists": true, "pending": true, "has_password": false
}}
// disabled/locked/deleted -> existe pero no disponible:
{ "is_valid": true, "code": 0, "data": {
  "exists": true, "unavailable": true
}}
```

NUNCA devuelve: la lista de metodos MFA, el password hash, el TOTP secret, los
recovery codes, el `credential_id` de las passkeys, ni datos de otro user
(AC-C6). Solo `exists` + `has_password` + flags de estado.

## Donde se revelan los metodos (NO en check-email)

- **`login.verify-password`** (fase B, ya devuelve `methods` en el step=2):
  tras verificar la password, el backend devuelve los metodos requeridos
  pendientes (`required_methods`) para el multi-factor. AQUI se conoce la lista.
- **`login.start` passwordless / `verify-magic-link` / `verify-code`**: tras el
  primer factor, el step-up (si hay metodos requeridos) los revela.
- En ambos casos el cliente ya paso UN factor antes de ver la lista -> sin
  reconnaissance pre-auth.

## 7.C Archivos afectados

### Crear — controller + modelo + service

- `core/controllers/login/check_email.py` — `CheckEmail(BaseController)`,
  `event_model=LoginCheckEmailIn`. `validate()` agrega Turnstile + rate-limit
  per-IP ANTES de tocar Neon (AC-C5). `execute()`:
  - Resuelve el user por email (lowercased).
  - None -> `{exists:false}`.
  - `pending` -> `{exists:true, pending:true, has_password:false}`.
  - `disabled`/`locked`/`deleted` -> `{exists:true, unavailable:true}`.
  - `active` -> `{exists:true, has_password:<bool>}` (consulta `has_password`
    via la fila `auth_credentials`; NO arma la lista de metodos).
- `core/models/login.py` — `LoginCheckEmailIn {email: EmailStr,
  cf_turnstile_response: str|None, meta}`.
  - Verificar: tests de controller (active+password, active sin password,
    not-found, pending, disabled, sin-turnstile, sin-datos-sensibles).

### Modificar — `login.verify-password` revela los metodos (ya en fase B)

- La fase B ya hace que `verify-password` devuelva `required_methods`/`methods`
  en el step=2. Aca solo se confirma que ESE es el punto donde se revela la
  lista (no `check-email`).

### Modificar — operations (sin cambio estructural)

- `core/settings/operations.py` — `login` ya registrada; el discovery toma
  `check_email.py` -> action `check-email`. Sin cambios.

## Mitigacion del riesgo de enumeracion

- **Turnstile obligatorio** en `check-email` (AC-C7): frena bots de enumeracion
  masiva. (El repo ya tiene auto-blacklist contra solvers de Turnstile.)
- **Rate-limit per-IP estricto** (AC-C5): regla dedicada agresiva (ej.
  10/min/IP) seedeada en las reglas de rate-limit.
- **Auditoria**: `check-email` se audita (`event='login.check-email'`).
- **El dato sensible (lista de metodos) NO se expone aca**: queda detras de la
  password (o del primer factor passwordless). Esto es la mitigacion principal,
  no Turnstile/rate-limit (que solo frenan el scraping de existencia).
- La existencia del email se expone deliberadamente (ya era enumerable):
  trade-off aceptado y documentado en `auth-system.md` (fase E).

## Tests requeridos (Bloque C)

- `tests/unit/controllers/login/test_check_email_active_with_password.py` ->
  `{exists:true, has_password:true}` [AC-C1].
- `test_check_email_active_no_password.py` -> `{exists:true,
  has_password:false}` [AC-C1].
- `test_check_email_not_found.py` -> `{exists:false}` [AC-C2].
- `test_check_email_pending.py` [AC-C3].
- `test_check_email_disabled_unavailable.py` [AC-C4].
- `test_check_email_no_turnstile.py` [AC-C7].
- `test_check_email_no_methods_no_sensitive_data.py` — asserta que la respuesta
  NO contiene la lista de metodos MFA NI hash/secret/credential_id [AC-C6, AC-C8].

[<- fase D](04-fase-d-fusion-login.md) | [Siguiente: fase A ->](06-fase-a-overview.md)
