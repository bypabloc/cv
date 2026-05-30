# 03 — Fase 2: orquestador captcha-o-bypass + transporte

[← 02 shared.crypto](02-fase-shared-crypto.md) · [Siguiente: Fase 3 →](04-fase-services-cleanup.md)

> Define DÓNDE se decide "bypass firmado vs CAPTCHA real" y renombra el
> transporte. Mantiene `shared.http.turnstile` httpx-puro.

## Parte A — orquestador `verify_captcha_or_bypass`

El bypass se mueve de `shared.http.turnstile` a `shared.crypto` para no
arrastrar `cryptography` a los consumidores de `shared.http`.

### Crear `shared/crypto/captcha.py`

- `verify_captcha_or_bypass(cf_response, *, remote_ip, bypass_token, stage) -> dict`:
  1. `cf_response` no vacío → delega en
     `shared.http.turnstile.verify_turnstile_token(cf_response, remote_ip=...)`.
  2. `cf_response` vacío:
     - `stage not in {'dev','local'}` → `TurnstileError(CAPTCHA_INVALID)` [AC-1].
     - `not bypass_token` → `TurnstileError(CAPTCHA_INVALID)`.
     - cargar pública (SSM `turnstile-bypass-public-key`, lazy via
       `get_secret_by_name`/`get_parameter`) →
       `verify_bypass_token(bypass_token, public_key_b64=pub, stage=stage)`.
     - ok → `{'success': True, 'hostname': 'bypass', 'bypassed': True}`.
     - `BypassTokenError` → log warning (sin token) +
       `TurnstileError(CAPTCHA_INVALID)`.
- Importa `shared.http.turnstile` + `shared.crypto.*`. `shared.http` NO
  depende de `shared.crypto` (la dependencia es al revés).

### Cambios en `shared.http.turnstile`

- ELIMINAR `_BYPASS_ALLOWED_STAGES`, `_load_bypass_secret`,
  `_try_bypass_turnstile` y el parámetro `bypass_secret`.
- La rama `cf_response` vacío pasa a lanzar `TurnstileError(CAPTCHA_INVALID)`
  directo.
- Conservar `resolve_origin` y la validación de hostname.
- Su test `test_turnstile.py`: quitar los 4 tests de bypass (migran a
  `shared/crypto/`), conservar los de siteverify/hostname. Actualizar el de
  `cf_response` vacío → ahora siempre `CAPTCHA_INVALID`.

## Parte B — transporte

### `shared/lambda_kit/http_dispatch.py`

- `bypass_secret = _header(headers, 'x-turnstile-bypass-secret')` →
  `bypass_token = _header(headers, 'x-turnstile-bypass-token')`.
- `_meta`: `'bypass_secret': bypass_secret` → `'bypass_token': bypass_token`.
- Actualizar docstring (línea ~197).
- Test `test_http_handler_injects_meta_from_headers.py`: usar
  `x-turnstile-bypass-token` + assert `'bypass_token'`.

### `shared/http/cors.py`

- `Access-Control-Allow-Headers`: `X-Turnstile-Bypass-Secret` →
  `X-Turnstile-Bypass-Token` (línea ~166).

## Verificación de la fase

```bash
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless lint-deps --shared
rg -n "cryptography|bypass_secret|_try_bypass" serverless/lambda/shared/http/
```

[← 02 shared.crypto](02-fase-shared-crypto.md) · [Siguiente: Fase 3 →](04-fase-services-cleanup.md)
