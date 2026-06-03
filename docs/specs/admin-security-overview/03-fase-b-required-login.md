# 03 — Fase B: Metodo requerido estricto + login multi-factor

[<- AC](02-criterios-aceptacion.md) | [Siguiente: fase D ->](04-fase-d-fusion-login.md)

> Agrega el concepto "metodo requerido al loguear": un flag `required` nuevo en
> los dos modelos de metodos, un `set-required`, y la logica de login que EXIGE
> todos los metodos requeridos (multi-factor), con fallback recovery/email-code
> anti-lockout. Cubre AC-B1..AC-B10.

## 7.B Archivos afectados

### Crear — migration Alembic

- `serverless/lambda/shared/db/alembic/versions/00000005_mfa_required_flag.py`
  — agrega `required BOOLEAN NOT NULL DEFAULT false` a `auth_mfa_methods` y
  `auth_webauthn_credentials`. `downgrade()` elimina ambas columnas.
  - Verificar: aplicar upgrade+downgrade+upgrade en un branch Neon de prueba
    (ver `neon-management.md`); `serverless run --stage=dev --lambda=db
    --event=events/migrate.json` + `events/current.json`.

### Modificar — modelos SQLAlchemy

- `serverless/lambda/shared/db/models/auth/mfa_method.py` — columna
  `required: Mapped[bool]` (default false, server_default).
- `serverless/lambda/shared/db/models/auth/webauthn_credential.py` — idem.
  - Verificar: `serverless tests --type=unit --shared`.

### Modificar — repository

- `serverless/lambda/shared/db/repositories/auth_mfa.py`:
  - `set_required(session, *, user_id, kind, required)` — setea `required` en
    el row `(user_id, kind)` activo. False si no existe/desactivado.
  - `set_webauthn_required(session, *, user_id, credential_id, required)` —
    idem por passkey activa.
  - `enable_mfa(session, *, user_id, kind)` — `disabled_at = NULL` SIN tocar
    `confirmed_at` (re-enable limpio del bloque A; se crea aca por cercania).
  - `enable_webauthn(session, *, user_id, credential_id)` — `disabled_at=NULL`.
  - `list_required_methods(session, *, user_id)` — devuelve los kinds MFA +
    passkeys con `required=true` y activos (lo consume el login).
  - Verificar: tests del repo en `shared/tests/unit/shared/db/`.

### Modificar — services auth

- `serverless/lambda/services/auth/core/services/mfa_method_service.py`:
  - `set_required(*, user_id, kind, required)` -> repo.
  - `enable(*, user_id, kind)` -> repo (re-enable).
  - `required_methods(*, user_id)` -> lista de tipos requeridos.
- `serverless/lambda/services/auth/core/services/webauthn_service.py`:
  - `set_required(*, user_id, credential_id, required)`, `enable(...)`.
  - Verificar: `serverless tests --type=unit --lambda=auth`.

### Crear — controllers + modelos

- `core/controllers/mfa/set_required.py` — `SetRequired(BaseController)`,
  `event_model=MfaSetRequiredIn`, `require_active_user`, 404 si no existe.
- `core/controllers/webauthn/set_required.py` — idem por `credential_id`.
- `core/models/mfa.py` — `MfaSetRequiredIn {kind: Literal['totp','email_code'],
  required: bool, meta}`.
- `core/models/webauthn.py` — `WebauthnSetRequiredIn {credential_id: UUID,
  required: bool, meta}`.
- `core/settings/operations.py` — sin cambio (mfa/webauthn ya registradas);
  el discovery por convencion toma `set_required.py` -> action `set-required`.
  - Verificar: tests de controller en `tests/unit/controllers/mfa/` y
    `webauthn/`.

### Modificar — login multi-factor (el cambio mas sensible)

El login hoy (tras password o passwordless) propone metodos y con UNO basta.
Con metodos requeridos hay que EXIGIR todos. Diseño:

- `core/controllers/login/_mfa_login.py` (helper compartido) — nueva funcion
  `required_or_terminal(*, user_id, ...)`: consulta `required_methods`; si hay
  >=1, emite un temp step=2 con `required_methods: [...]` y `satisfied: []` en
  los claims (o en un store), en vez de tokens; si no hay requeridos, mantiene
  el comportamiento actual (propone, con uno basta).
- `core/controllers/login/verify_password.py` y `verify_totp.py` y
  `webauthn/login_verify.py`:
  - Tras verificar un factor, marcar ese metodo como "satisfecho" en el temp
    step=2 (rotando el temp con la lista `satisfied` actualizada).
  - Emitir access+refresh SOLO cuando `satisfied >= required_methods`.
- `core/controllers/mfa/recovery_codes_consume.py` — el recovery code SALTEA
  los requeridos (fallback AC-B7): emite tokens directo.
- `core/controllers/login/verify_code.py` (email-code) — cuando se usa como
  **emergencia** (hay metodos requeridos pendientes), emite tokens igual
  (fallback AC-B8) y audita `login.emergency_email_code`.
  - Verificar: tests de los escenarios B5-B9 (multi-required, parcial,
    recovery-bypass, email-emergencia).

### Modificar — `mfa.list` y respuestas existentes

- `mfa_method_service.list_active` y `webauthn_service.list_credentials` —
  agregar `required` al dict devuelto (lo consume el overview del bloque A y
  la UI). NO romper los campos existentes (`kind`, `preferred`, `confirmed`).
  - Verificar: tests existentes de `mfa.list` ajustados al nuevo campo.

## Decision de diseño del temp step=2 (multi-factor)

El temp JWT step=2 hoy es opaco (solo `flow`, `step`, `sub`). Para multi-factor
necesitamos rastrear que factores ya se satisficieron sin un store server-side
extra. Opciones evaluadas y elegida:

- **Elegida**: codificar `satisfied: [...]` y `required: [...]` en los claims
  del temp step=2 (el temp se rota en cada verify, blacklisteando el anterior
  — patron rolling ya existente). Sin tabla nueva, sin estado server-side.
- Descartada: una tabla `login_challenges` (overkill; el temp rolling ya da el
  rastreo y la expiracion).

## Riesgo y mitigacion (lockout)

- El fallback recovery-code + email-code de emergencia es OBLIGATORIO en el
  diseño: NUNCA un user queda sin escape (AC-B7, AC-B8).
- La UI (bloque E) advierte al marcar "requerido": "Guarda tus codigos de
  recuperacion; si pierdes este metodo solo podras entrar con un recovery code
  o el codigo de emergencia por email."

## Tests requeridos (Bloque B)

- `shared/tests/.../test_mfa_required_columns.py` — la migration agrega las 2
  columnas; el modelo las expone [AC-B1].
- `tests/unit/controllers/mfa/test_set_required_*.py` — ok / 404 / toggle
  off [AC-B2, AC-B4, AC-B10].
- `tests/unit/controllers/webauthn/test_set_required_*.py` [AC-B3].
- `tests/unit/controllers/login/test_login_multi_required_*.py` — 2 requeridos
  exige ambos; parcial no emite tokens; recovery saltea; email-emergencia
  saltea [AC-B5..AC-B9].
- `tests/unit/services/test_mfa_method_service_required.py`,
  `test_enable.py` [AC-B2, AC-A6].

[<- AC](02-criterios-aceptacion.md) | [Siguiente: fase D ->](04-fase-d-fusion-login.md)
