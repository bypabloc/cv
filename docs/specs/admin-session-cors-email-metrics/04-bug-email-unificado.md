# 04 — Bug 3: magic-link + code en un solo email

[<- 03](03-bug-cors-authorization.md) | [Bug 4 ->](05-bug-metrics-navitem.md)

Backend (`auth`). Redeploy `auth` + `seed-email-config`. NO redeploy
`send_email` (solo lee la tabla).

## Estado actual (2 emails por request)

- `register/start.py:168-183`: `publish_magic_link(kind='register-magic-link',
  verify_url, expires_in=LINK_TTL_MINUTES)` + `publish_code(kind='register-code',
  code, expires_in=CODE_TTL_MINUTES)`.
- `login/start.py:192-207`: idem con `login-*`.
- `verify/resend_code.py:171-186`: idem con `f'{flow}-magic-link'` /
  `f'{flow}-code'` (flow = `claims.flow`, `register`|`login`).

`code` y `token` ya se generan en el MISMO `execute()`. `CODE_TTL_MINUTES ==
LINK_TTL_MINUTES == 15`.

## Diseno (decision: kind unificado nuevo + 1 template)

1. `email_dispatch_service.py` — `publish_unified(*, to, user_id, niche, kind,
   verify_url, code, expires_in_min)` -> `_publish(kind, to, data={verify_url,
   code, expires_in_min})`. Mantener `publish_magic_link`/`publish_code` por
   compat (solo dejan de llamarse en los controllers).
2. Controllers — reemplazar las 2 llamadas por 1:
   - `register/start.py`: `publish_unified(kind='register-unified',
     verify_url, code, expires_in_min=15)`.
   - `login/start.py`: `kind='login-unified'`.
   - `verify/resend_code.py`: `kind=f'{claims.flow}-unified'` (resuelve a
     register-unified/login-unified; sin tercer kind).
3. `send_email/seeds/email_config.py` — filas:
   - `{'kind': 'register-unified', 'subject': 'Confirma tu cuenta en The Full Stack'}`
   - `{'kind': 'login-unified', 'subject': 'Tu acceso a The Full Stack'}`
4. Templates nuevos (4 archivos en `send_email/seeds/templates/`):
   `register-unified.html/.txt`, `login-unified.html/.txt`. Cada uno: boton
   `{{ verify_url }}` + bloque `{{ code }}` (alternativa) + `{{ expires_in_min }}`.

## Edge-cases / riesgos

- **TTL unico**: ambos TTL son 15 min -> `expires_in_min=15` sin ambiguedad.
- **Orden seed vs deploy**: si `auth` envia `register-unified` antes de que la
  fila exista en `email-config`, `send_email` no encuentra el template ->
  correr `seed-email-config` ANTES/junto al redeploy de `auth`.
- **Compat**: los kinds/templates viejos (`*-code`, `*-magic-link`) se
  mantienen -> emails en vuelo y rollback no rompen.
- **`niche` en resend es `None`**: `publish_unified` acepta `niche: str | None`.
- **`users` email service**: NO se toca (kinds distintos, no combina).

## Tests (Lambda auth, mirror en `services/auth/tests/unit/`)

- `services/test_email_dispatch_service.py`: `publish_unified` -> 1 invoke con
  `data={verify_url, code, expires_in_min}` [AC-7].
- `controllers/register/test_register_start_new_email_ok.py`:
  `publish_unified.assert_called_once()` + viejos no llamados [AC-8].
- `controllers/login/test_login_start_email_active_no_password.py` [AC-9].
- `controllers/verify/test_verify_resend_code_ok.py`: kind por flow [AC-9].
- Anti-enumeration: `register_start_email_active_409`,
  `login_start_email_locked_404`, `verify_resend_code_throttled` ->
  `publish_unified.assert_not_called()` [AC-10].
- Seed test en `devtools/tests/unit/src/serverless/email_seed.py` si asserta
  kinds.

## Deploy

- Redeploy `auth`: SI (cambio codigo). Redeploy `send_email`: NO.
- `serverless seed-email-config --stage=dev`: SI (sube 4 templates + 2 filas).
