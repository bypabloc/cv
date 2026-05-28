# 07. Archivos Afectados — plan 02

## Crear

### Migration + modelos Neon

- `serverless/lambda/shared/db/alembic/versions/00000003_auth_mfa.py`
  — migration con 3 tablas (`auth_mfa_methods`,
  `auth_mfa_recovery_codes`, `auth_webauthn_credentials`) + enum
  `auth_mfa_kind`.
  - Verificar: en branch Neon de prueba aplicar up + down + up
    idempotente.
- `serverless/lambda/shared/db/models/auth/mfa_method.py`
- `serverless/lambda/shared/db/models/auth/recovery_code.py`
- `serverless/lambda/shared/db/models/auth/webauthn_credential.py`
- `serverless/lambda/shared/db/models/auth/enums.py` — agregar
  `AuthMfaKind` al archivo existente del plan 01.
- `serverless/lambda/shared/db/models/auth/__init__.py` — re-export
  los nuevos.
- `serverless/lambda/shared/db/repositories/auth_mfa.py` — helpers
  para los 3 dominios + tests (~14 archivos).
  - Verificar: `serverless tests --type=unit --shared`.

### Shared.auth extension (TOTP + WebAuthn + recovery codes)

- `serverless/lambda/shared/auth/totp.py` — pyotp wrappers (sin QR).
- `serverless/lambda/shared/auth/webauthn.py` — fido2 wrappers (post-spike).
- `serverless/lambda/shared/auth/recovery_codes.py`.
- `serverless/lambda/shared/auth/__init__.py` — agregar re-exports.
- `serverless/lambda/shared/auth/pyproject.toml` — agregar SOLO pyotp +
  python-fido2. NO `cryptography`, NO `segno` (decision 1 + 8 del README).
- `serverless/lambda/shared/auth/uv.lock` — regenerar con `uv lock`.
- `serverless/lambda/shared/tests/unit/shared/auth/` — 13 archivos
  nuevos (listados en seccion 03; menos que la version inicial — sin
  envelope encryption ni QR SVG).

### Shared.aws (KMS wrappers — CMK directa)

- `serverless/lambda/shared/aws/kms.py` — `kms_encrypt` +
  `kms_decrypt` (KMS Encrypt/Decrypt directos, sin
  GenerateDataKey).
- `serverless/lambda/shared/aws/__init__.py` — agregar re-exports.
- `serverless/lambda/shared/aws/pyproject.toml` — sin cambios (boto3
  ya esta declarado).
- `serverless/lambda/shared/tests/unit/shared/aws/test_kms_*.py` — 4
  tests con moto (listados en seccion 03).

  - Verificar: `serverless lint-deps --shared` +
    `serverless tests --type=unit --shared`.

### Infra (resources/)

- `serverless/lambda/resources/dynamodb/webauthn-challenges.yaml` —
  PK `challenge_id`, TTL `expires_at`.
  - Verificar:
    `serverless validate-catalog --stage=dev`
    `serverless provision-infra --stage=dev --aws-profile=tfs-dev`

### Lambda `auth` extension

- `serverless/lambda/services/auth/manifest.yaml` — MODIFICAR
  agregando:
  - `uses.tables.webauthn-challenges: read-write`
  - `uses.kms` con `alias/portfolio-lambdas` + actions
    `Encrypt`, `Decrypt` (CMK directa, decision 1)
  - env vars `KMS_TOTP_KEY_ID`, `WEBAUTHN_RP_ID`,
    `WEBAUTHN_RP_NAME`, `WEBAUTHN_ALLOWED_ORIGINS`
- `serverless/lambda/services/auth/core/settings/config.py` —
  MODIFICAR agregando properties (`kms_totp_key_id`,
  `webauthn_rp_id`, `webauthn_rp_name`, `webauthn_allowed_origins`,
  `webauthn_challenges_table`).
- `serverless/lambda/services/auth/core/settings/operations.py` —
  MODIFICAR agregando `mfa` y `webauthn` (+ actions nuevas de
  `login`).
- `serverless/lambda/services/auth/core/models/event.py` — MODIFICAR
  agregando las nuevas operations al `build_event_model()`.
- `serverless/lambda/services/auth/core/models/mfa.py` — Pydantic
  schemas (8 actions).
- `serverless/lambda/services/auth/core/models/webauthn.py` — Pydantic
  schemas (6 actions).
- `serverless/lambda/services/auth/core/models/login.py` — MODIFICAR
  agregando `LoginVerifyPasswordIn`, `LoginVerifyTotpIn`.

- `serverless/lambda/services/auth/core/controllers/mfa/__init__.py`
- `serverless/lambda/services/auth/core/controllers/mfa/{setup_totp,confirm_totp,setup_email_code,set_preferred,disable,list,recovery_codes_generate,recovery_codes_consume}.py`
- `serverless/lambda/services/auth/core/controllers/webauthn/__init__.py`
- `serverless/lambda/services/auth/core/controllers/webauthn/{register_options,register_verify,login_options,login_verify,list_credentials,delete_credential}.py`
- `serverless/lambda/services/auth/core/controllers/login/{verify_password,verify_totp}.py` — NUEVOS

- `serverless/lambda/services/auth/core/services/{mfa_method,totp,webauthn,recovery_codes,challenge,auth}_service.py` — NUEVOS (6 services nuevos).

- `serverless/lambda/services/auth/events/mfa-*.json` (8 archivos).
- `serverless/lambda/services/auth/events/webauthn-*.json` (6 archivos).
- `serverless/lambda/services/auth/events/login-verify-password.json`,
  `login-verify-totp.json`.

- `serverless/lambda/services/auth/tests/unit/services/test_*.py` (~25 nuevos).
- `serverless/lambda/services/auth/tests/unit/controllers/test_mfa_*.py` (~15).
- `serverless/lambda/services/auth/tests/unit/controllers/test_webauthn_*.py` (~10).
- `serverless/lambda/services/auth/tests/unit/controllers/test_login_*.py` (~5 nuevos).
- `serverless/lambda/services/auth/tests/unit/models/test_mfa_*.py` (~5).
- `serverless/lambda/services/auth/tests/unit/models/test_webauthn_*.py` (~5).
- `serverless/lambda/services/auth/tests/unit/controllers/webauthn/_fixtures.py` — helpers SoftWebauthnDevice.
- `serverless/lambda/services/auth/tests/integration/test_mfa_*.py` y `test_webauthn_*.py` (~7 archivos).

  - Verificar:
    `serverless lint-deps --lambda=auth`
    `serverless tests --type=unit --lambda=auth`
    `serverless tests --type=coverage --lambda=auth` (>= 85%)

### Documentacion permanente

- `.claude/docs/auth-system/04-mfa.md` — NUEVO (TOTP setup, recovery
  codes, login con MFA).
- `.claude/docs/auth-system/05-webauthn.md` — NUEVO (Passkeys, RP_ID,
  sign_count, clone detection).
- `.claude/rules/auth-system.md` — MODIFICAR agregando seccion MFA +
  WebAuthn.
- `.claude/rules/lambda-shared-imports.md` — MODIFICAR el catalogo de
  portadores (agregar pyotp, python-fido2, boto3.kms). NO se agrega
  `cryptography` ni `segno` (decision 1 + 8).
- `.claude/skills/auth-system/SKILL.md` — MODIFICAR el frontmatter
  para incluir keywords MFA + WebAuthn (`mfa`, `totp`, `passkey`,
  `webauthn`, `2fa`, `autenticacion en dos pasos`, `factor doble`).

## Modificar

- `docs/diagrams/db-er.mmd` — agregar las 3 tablas nuevas
  (`auth_mfa_methods`, `auth_mfa_recovery_codes`,
  `auth_webauthn_credentials`) + relacion FK a `auth_users`.
- `docs/specs/02-auth-mfa/` — esta carpeta del plan (efimera, se
  elimina en commit final).
- `serverless/lambda/services/auth/manifest.yaml` — listado arriba
  como modificar.
- `serverless/lambda/services/auth/core/settings/{config,operations}.py`
  — modificacion incremental.
- `serverless/lambda/services/auth/core/models/event.py` —
  modificacion incremental.
- `serverless/lambda/services/auth/core/models/login.py` — agregar
  schemas nuevos.

- `devtools/serverless/provisioner.py` — POSIBLEMENTE modificar si
  el manifest no soporta `uses.kms` declarativo (verificar primero;
  si soporta, no se toca). Es un cambio menor (~50 lineas).

## Eliminar

- `docs/specs/02-auth-mfa/` — al cerrar el plan (ultimo commit).

## NO se toca

- Frontend Astro.
- Lambdas `cv`, `contact_form`, `contact_worker`, `tracking_pixel`,
  `tracking_worker`, `stream_processor`, `auth_email_worker`, `db`.
- Shared subpackages `core`, `db`, `http`, `observability`,
  `rate_limit`, `cache`, `dynamodb`, `lambda_kit` (excepto los
  delta indicados arriba en `shared.aws` y `shared.auth`).
- `.github/workflows/*.yml`.

## Resumen contable

| Categoria | Crear | Modificar | Eliminar | Total |
|-----------|-------|-----------|----------|-------|
| Migration Alembic | 1 | 0 | 0 | 1 |
| Modelos SQLAlchemy + repositories | 4 + ~14 tests | 1 | 0 | ~19 |
| `shared.auth/` (impl + tests + pyproject) | 16 (3 modulos + 13 tests) | 2 | 0 | 18 |
| `shared.aws/` (impl + tests KMS) | 5 (1 modulo + 4 tests) | 1 | 0 | 6 |
| Infra resources | 1 | 0 | 0 | 1 |
| Lambda `auth` (controllers + services + models + events + tests) | ~85 | 5 | 0 | 90 |
| Documentacion permanente (.claude/) | 2 | 3 | 0 | 5 |
| Plan efimero (`docs/specs/02-...`) | 12 | 0 | -12 | 0 |
| Diagrama ER | 0 | 1 | 0 | 1 |
| Devtools provisioner (post-spike, condicional) | 0 | 0 o 1 | 0 | 0 o 1 |
| **Total neto** | | | | **~140 archivos** (vs ~147 inicial — sin `encryption.py` ni `segno`) |
