# 04 — Fase 3: wiring de servicios + limpieza

[← 03 verifier](03-fase-verifier-transport.md) · [Siguiente: Fase 4 →](05-fase-devtools.md)

> Conecta `contact_form` y `auth` al orquestador nuevo y elimina el campo
> `bypass_secret` muerto de `tracking_pixel` y `cv`.

## `contact_form`

- `core/models/contact.py`: `RequestMeta.bypass_secret` → `bypass_token`.
- `core/controllers/contact/create.py`:
  - import `from shared.http.turnstile import verify_turnstile_token` →
    `from shared.crypto.captcha import verify_captcha_or_bypass`.
  - el call (línea ~136) → `verify_captcha_or_bypass(data.cf_token,
    remote_ip=meta.ip, bypass_token=meta.bypass_token, stage=<STAGE>)`.
- `core/settings/config.py`: `ssm_turnstile_bypass_path` →
  `ssm_turnstile_bypass_public_key_path`.
- `manifest.yaml`: env `SSM_TURNSTILE_BYPASS_SECRET_PATH` →
  `SSM_TURNSTILE_BYPASS_PUBLIC_KEY_PATH`
  (`/portfolio/${stage}/turnstile-bypass-public-key`). IAM: la pública es
  String → NO `kms:Decrypt` para este param.
- `core/handler.py`: docstring que menciona "bypass-secret".
- Tests: `_helpers.py`, `test_request_meta_accepts_authorization.py`,
  `test_contact_model_accepts_valid_form.py`,
  `test_auto_blacklist_runs_in_both_modes.py`,
  `test_create_controller_normalizes_success.py` → `bypass_secret` →
  `bypass_token`. `tests/integration/test_turnstile_bypass_secret_e2e.py` →
  reescribir firmando un token. `events/create_bypass.json` → regenerar.
  Agregar `test_bypass_rejected_in_prod.py` [AC-1].

## `auth`

- `core/models/_common.py`: `_Meta.bypass_secret` → `bypass_token`.
- `core/controllers/register/start.py` (línea ~69) y
  `core/controllers/login/start.py` (línea ~65): el call →
  `verify_captcha_or_bypass(data.cf_turnstile_response, remote_ip=meta.ip,
  bypass_token=meta.bypass_token, stage=<STAGE>)`.
- `core/settings/config.py` (línea ~211): `@cached_property
  turnstile_bypass_secret` → `turnstile_bypass_public_key`. SSM name
  `turnstile-bypass-secret` → `turnstile-bypass-public-key`.
- `manifest.yaml`: mismo cambio de env var + IAM.
- Tests: `controllers/_helpers.py`, `conftest.py`,
  `controllers/login/test_login_start_with_password_*`,
  `models/test_register_start_in_turnstile_required.py` → token firmado.
  Agregar `test_register_start_bypass_rejected_in_prod.py` [AC-1].

## `tracking_pixel` (limpieza — NO valida Turnstile)

- `core/models/tracking.py`: ELIMINAR `bypass_secret` de `TrackEventMeta`
  (si existe) [AC-10].
- `tests/unit/test_track_meta_accepts_authorization.py` → quitar bypass.

## `cv` (limpieza — NO valida Turnstile)

- `core/models/cv.py` (línea ~28): ELIMINAR `bypass_secret` [AC-10].
- `tests/unit/test_cv_meta_accepts_authorization.py` → quitar bypass.

> El `_meta` que inyecta `http_dispatch` ahora trae `bypass_token`;
> `tracking_pixel`/`cv` lo ignoran si su `_Meta` usa `extra='ignore'`.
> Confirmar el `model_config` de cada uno.

## Verificación de la fase

```bash
for L in contact_form auth tracking_pixel cv; do
  python devtools/run.py serverless tests --type=unit --lambda=$L
done
python devtools/run.py serverless tests --type=coverage --lambda=contact_form
python devtools/run.py serverless tests --type=coverage --lambda=auth
python devtools/run.py serverless lint-deps
python devtools/run.py serverless lint-deps --lambda=tracking_pixel  # sin cryptography
python devtools/run.py serverless lint-deps --lambda=cv              # sin cryptography
```

[← 03 verifier](03-fase-verifier-transport.md) · [Siguiente: Fase 4 →](05-fase-devtools.md)
