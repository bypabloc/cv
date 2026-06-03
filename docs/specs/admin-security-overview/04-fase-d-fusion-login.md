# 04 — Fase D: Fusion register -> login

[<- fase B](03-fase-b-required-login.md) | [Siguiente: fase C ->](05-fase-c-check-email.md)

> Elimina la operation `register` (3 actions + controllers + tests + UI). Su
> logica se mueve a `login`: `login.start` crea el user `pending` si el email no
> existe; `verify-code`/`verify-magic-link` detectan `pending -> active` por el
> status del user, con flow unico `login`. Cubre AC-D1..AC-D9.

## Por que esta fase va DESPUES de B

B agrega la migration y el login multi-factor. D modifica `login.start` y los
`verify-*`, que tienen que convivir con el multi-factor de B. Hacer D sobre el
login ya tocado por B evita un segundo refactor del mismo archivo.

## 7.D Archivos afectados

### Modificar — `login.start` (absorbe register.start)

- `core/controllers/login/start.py`:
  - Hoy: email inexistente -> 404 `EMAIL_NOT_FOUND` + `suggest_register`.
  - Nuevo: email inexistente -> **crea el user `pending`**
    (`user_svc.create_pending`), genera code + magic-link, invoca
    `publish_unified(kind='login-unified', ...)`, devuelve `temp_token`
    (flow `login`, step 1) + `created: true`.
  - Email `pending` -> re-emite artefactos (no 409); `created: false`,
    `pending: true`.
  - Email `active` -> comportamiento actual (passwordless o password).
  - Quitar el branch `PENDING_VERIFICATION` 409 (ahora se re-emite).
  - Mantener Turnstile + rate-limit + anti-enumeration de estados disabled/
    locked (esos SIGUEN ocultos; solo el "no existe" cambia a "crear").
  - Verificar: tests de `login.start` (nuevo: crea pending; re-emite pending;
    active passwordless; active password).

### Modificar — `login.verify-code` (cierra pending -> active)

- `core/controllers/login/verify_code.py`:
  - Tras validar el code, si el user esta `pending` -> `user_svc.mark_active`
    (cierra el registro); si ya `active` -> solo `update_last_login`.
  - El `temp_token` esperado es `flow='login'` (ya no `register`).
  - Verificar: test pending->active + test active-solo-login.

### Modificar — `login.verify-magic-link` (cierra pending -> active)

- `core/controllers/login/verify_magic_link.py` — idem: pending -> active;
  active -> solo login. `flow='login'`.
  - Verificar: test pending->active via magic-link.

### Eliminar — la operation `register` completa

- `core/controllers/register/` (carpeta entera: `start.py`, `verify_code.py`,
  `verify_magic_link.py`, `__init__.py`).
- `core/settings/operations.py` — quitar la entry `'register'`.
- `core/models/register.py` (si existe) — eliminar.
- Los tests de register: `tests/unit/controllers/register/` (carpeta entera).
  - Verificar: `serverless tests --type=unit --lambda=auth` (sin referencias
    colgantes a register); `python -m compileall core`.

### Modificar — verify.resend-code (flow unico)

- `core/controllers/verify/resend_code.py` — usa `claims.flow` para el kind del
  email (`f'{flow}-unified'`). Con flow unico `login`, el kind es siempre
  `login-unified`. Simplificar a `login-unified`.
  - Verificar: test resend con flow login.

### Modificar — email config (consolidar kinds)

- `serverless/lambda/services/send_email/seeds/email_config.py` — eliminar las
  filas `register-unified` (y cualquier `register-*` residual); dejar
  `login-unified` como el unico kind del flujo de entrada.
- `serverless/lambda/services/send_email/seeds/templates/` — eliminar
  `register-unified.{html,txt}` si el contenido es identico a
  `login-unified.{html,txt}`; si difieren, unificar el copy en `login-unified`.
  - Verificar: `serverless seed-email-config --stage=dev` no falla; el envio
    real usa `login-unified` (Bloque Z).

### Frontend (se detalla en fase E, listado aqui para trazabilidad)

- Eliminar: `app/(auth)/register/page.tsx`, `register-form.tsx`,
  `use-register-start.ts`, `use-register-verify-code.ts`,
  `authClient.registerStart`/`registerVerifyCode`, `ROUTES.auth.register`,
  `registerSchema`.
- Migrar la logica a `login` (fase E).

## Edge cases

- **Idempotencia**: `login.start` de un email `pending` re-emite (invalida los
  code/link previos) — mismo patron que hoy hace `register.start` con un
  `pending` existente.
- **Crear cuenta sin confirmacion**: el user `pending` NO es funcional hasta
  verificar (no tiene sesion, no puede operar). Esto acota el abuso de "crear
  cuentas": un atacante solo crea filas `pending` inertes (mitigado por
  rate-limit + Turnstile).
- **Anti-enumeration de estados**: disabled/locked SIGUEN devolviendo un body
  que no revela el estado real al cliente (solo "no disponible"); lo que cambia
  es que "no existe" ahora ofrece crear (decision D + C).

## Tests requeridos (Bloque D)

- `tests/unit/controllers/login/test_login_start_creates_pending.py` [AC-D2].
- `test_login_start_existing_active.py` [AC-D3].
- `test_login_verify_code_pending_activates.py` [AC-D4].
- `test_login_verify_magic_link_pending_activates.py` [AC-D5].
- `test_login_verify_code_active_only_login.py` [AC-D6].
- Barrido: `rg -l "operation.*register|controllers/register|registerStart"`
  -> CERO en `services/auth/core` y `admin/src` tras la fase [AC-D1, AC-D9].

[<- fase B](03-fase-b-required-login.md) | [Siguiente: fase C ->](05-fase-c-check-email.md)
