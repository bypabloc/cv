# MFA — TOTP, email-code, recovery codes y login con password

> [< README](README.md) | [< 03-rate-limit-rules](03-rate-limit-rules.md)
> | [05-webauthn >](05-webauthn.md)
>
> Extension del plan 02-auth-mfa al Lambda `auth`. Cubre la operation
> `mfa` (8 actions), las 2 actions nuevas de `login` (verify-password,
> verify-totp) y la columna `auth_users.sessions_revoked_at`.

## TOTP (RFC 6238)

`mfa.setup-totp` genera un secret de 20 bytes (160 bits) en base32 via
`generate_totp_secret_b32()` (`pyotp.random_base32`). Devuelve
`{secret_b32, otpauth_url}` — el **frontend** renderiza el QR del
`otpauth_url`; el backend NO devuelve SVG (sin dep `segno`).

El secret se cifra ANTES de persistir con `kms:Encrypt` sobre la CMK
directa `alias/portfolio-lambdas`:

```python
ciphertext = kms_encrypt(
    plaintext=secret_b32.encode('utf-8'),
    key_id=app_config.kms_totp_key_id,          # alias/portfolio-lambdas
    encryption_context={'user_id': str(user.id), 'purpose': 'totp'},
)
```

- **CMK directa, SIN envelope** (decision 1): el secret de 20 bytes entra
  holgado en el limite de 4 KB de `kms:Encrypt`. Sin `GenerateDataKey`,
  sin AES-GCM propio, sin nonce. Schema: 1 sola columna
  `auth_mfa_methods.totp_secret_ciphertext` (BYTEA).
- El `EncryptionContext` queda bindeado al ciphertext: el `kms_decrypt`
  debe pasar el MISMO context o falla. Binding criptografico al `user_id`
  + audit en CloudTrail.
- `setup-totp` guarda un row `auth_mfa_methods` con `kind=totp`,
  `confirmed_at=NULL` (pendiente). Requiere **access JWT** valido.

`mfa.confirm-totp` recibe un `code` de 6 digitos, lo verifica con
`verify_totp_code(secret_b32, code, valid_window=1)` — `valid_window=1`
acepta el code actual + el anterior + el siguiente (cubre clock drift de
hasta 30s en cada direccion). Si OK: marca `confirmed_at=now()`, y si es
el primer metodo confirmado lo marca `preferred=true`. Devuelve 204.

## Email-code como 2do factor

`mfa.setup-email-code` activa `email_code` como metodo MFA. Como el user
ya probo recibir email en register, el metodo se inserta **confirmado de
inmediato** (`confirmed_at=now()`). Reusa el code de 8 chars del plan 01
(`shared.auth.codes`), promovido a 2do factor cuando el user ya se
autentico con un factor fuerte.

> `email_code` NO se ofrece en `methods` post-password — el login con MFA
> solo propone `['totp', 'webauthn']` (decision 10). El recovery code
> exige tambien un factor fuerte (ver abajo).

## Recovery codes

`mfa.recovery-codes-generate` emite 10 codes de 10 chars en alfabeto
Crockford-like `ABCDEFGHJKMNPQRSTUVWXYZ23456789` (sin O/0/I/1/L, espacio
30^10 ~ 5.9x10^14) via `secrets.choice` (CSPRNG). Se muestran **UNA sola
vez** en la response; el backend guarda solo el hash SHA-256
(`auth_mfa_recovery_codes.code_hash`, UNIQUE). Tabla aparte (no JSONB)
para auditar el consumo individual. Regenerar borra los 10 viejos y emite
10 nuevos.

`mfa.recovery-codes-consume` es un **bypass MFA durante el login** — NO
usa `require_active_user` (el user aun no tiene access JWT). Verifica un
`temp_token` step=2 que SOLO existe tras un factor fuerte:

```python
_STRONG_FLOW = 'login-mfa'   # producido tras password / webauthn
_STRONG_STEP = 2
if claims.flow != _STRONG_FLOW or claims.step != _STRONG_STEP:
    return 403 RECOVERY_REQUIRES_STRONG_FACTOR   # AC-9b, decision 10
```

> Desviacion del plan: `JwtClaims` tiene `extra='forbid'` y NO admite un
> claim `prev`. El factor previo se codifica con `flow='login-mfa'`: los
> flujos passwordless (magic-link / email-code) nunca emiten un step=2
> con ese flow, asi que el gate los excluye. `compare_recovery_code` usa
> `secrets.compare_digest` (constant-time). Un code ya consumido -> 400
> RECOVERY_CODE_CONSUMED. Al exito: blacklistea el temp + emite
> access+refresh con `family_id` nuevo.

## set-preferred / disable y el guard MUST_KEEP_ONE_MFA_METHOD

`mfa.set-preferred` cambia el metodo por defecto entre los activos.
`mfa.disable` deshabilita un metodo (`disabled_at=now()`).

`count_active_mfa` es una **cuenta transversal**: `auth_mfa_methods`
activos (`confirmed_at NOT NULL` + `disabled_at NULL`) MAS
`auth_webauthn_credentials` activos (`disabled_at NULL`). Si la operacion
dejaria al user en `total_mfa == 0` -> `409 MUST_KEEP_ONE_MFA_METHOD`
(AC-5, AC-17). Un user con 1 TOTP + 1 passkey puede borrar el passkey
(le queda TOTP). Intentar `disable` con un metodo de otro user -> `404
NOT_FOUND` (anti-enumeration, AC-5b). `mfa.list` (GET) devuelve los
metodos activos del user.

## Login con password (extension de plan 01)

`login.start` acepta `{email, cf_turnstile_response, password?}`:

```text
login.start
  email no existe        -> 404 EMAIL_NOT_FOUND, suggest_register=true
  pending                -> 409 PENDING_VERIFICATION
  disabled/locked        -> 404 EMAIL_NOT_FOUND, suggest_register=false (anti-enum)
  password ausente       -> flujo passwordless del plan 01 (magic-link + code)
  password presente:
    argon2 no matchea     -> 401 INVALID_PASSWORD + failed_attempts++ (AC-21)
    argon2 OK + sin MFA   -> access+refresh directo (AC-20)
    argon2 OK + con MFA   -> temp JWT flow='login-mfa' step=2
                             + methods=['totp','webauthn'] (AC-18)
```

`login.verify-password` y `login.verify-totp` (NUEVAS) completan el paso
2. `login.verify-totp` recibe el temp step=2 + `code`, valida el TOTP
confirmado del user (decrypt del secret via `kms_decrypt` en
`TotpService`), blacklistea el temp, marca `last_used_at` del metodo y
emite access+refresh con `family_id` nuevo (helper `issue_terminal_tokens`).

## AC-27 — revocar sesiones al confirmar el PRIMER MFA

Cuando un user pasa de `total_mfa: 0 -> 1` (confirma su primer metodo via
`mfa.confirm-totp`, `mfa.setup-email-code` o `webauthn.register-verify`),
el side-effect revoca todas las sesiones previas:

```python
# MfaMethodService.confirm() / setup_email_code() / WebauthnService.persist_credential()
before = count_active_mfa(session, user_id=...)
# ... INSERT/UPDATE ...
after = count_active_mfa(session, user_id=...)
if before == 0 and after == 1:
    SessionService(app_config).revoke_all_for_user(user_id=...)
```

`revoke_all_for_user` setea `auth_users.sessions_revoked_at = now()`.
`session.refresh` rechaza con `401 TOKEN_FAMILY_REVOKED` cualquier
refresh JWT cuyo `iat` sea anterior a ese timestamp. Razon: cerrar la
ventana donde un atacante con un refresh previo seguiria operando sin
pasar MFA (decision 15).

## Las 8 actions de `mfa` + 2 nuevas de `login`

| operation.action | Metodo | Que hace |
|---|---|---|
| `mfa.setup-totp` | POST | Genera secret + otpauth_url; row pendiente. Requiere access JWT |
| `mfa.confirm-totp` | POST | Verifica primer code 6-digit -> activa el metodo |
| `mfa.setup-email-code` | POST | Activa email_code como MFA (confirmado de inmediato) |
| `mfa.set-preferred` | POST | Cambia el preferred entre metodos activos |
| `mfa.disable` | POST | Deshabilita un metodo (guard MUST_KEEP_ONE) |
| `mfa.list` | GET | Lista los metodos MFA activos del user |
| `mfa.recovery-codes-generate` | POST | Emite 10 codes (muestra UNA vez) |
| `mfa.recovery-codes-consume` | POST | Consume 1 code (bypass MFA, exige factor fuerte) |
| `login.verify-password` | POST | NUEVA — paso 2a tras start con password |
| `login.verify-totp` | POST | NUEVA — paso 3 si MFA configurado |

## Codigos de error

| Codigo | Significado |
|---|---|
| `INVALID_TOTP_CODE` | code TOTP no matchea el secret |
| `MFA_NOT_CONFIGURED` | el user no tiene el metodo requerido |
| `MUST_KEEP_ONE_MFA_METHOD` | disable/delete dejaria al user con total_mfa==0 (transversal) |
| `RECOVERY_REQUIRES_STRONG_FACTOR` | recovery-codes-consume sin temp step=2 login-mfa (AC-9b) |
| `RECOVERY_CODE_CONSUMED` | code ya usado |
| `INVALID_PASSWORD` | password no matchea (login con password) |
| `TOKEN_FAMILY_REVOKED` | refresh con iat anterior a sessions_revoked_at (AC-27) |

---

[< README](README.md) — knowledge tree del dominio auth.
