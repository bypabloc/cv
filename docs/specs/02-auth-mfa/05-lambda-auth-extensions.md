# 05. Lambda `auth` — extensiones MFA + WebAuthn

## Nuevas operations y actions

```text
operation 'mfa' (8 actions):
- setup-totp                POST  -> genera secret + QR
- confirm-totp              POST  -> verifica primer code -> activa
- setup-email-code          POST  -> marca email_code como metodo
- set-preferred             POST  -> cambia preferred entre activos
- disable                   POST  -> deshabilita un metodo (no si es unico)
- list                      GET   -> lista metodos activos del user
- recovery-codes-generate   POST  -> emite 10 codes (muestra UNA vez)
- recovery-codes-consume    POST  -> consume 1 code (bypass MFA)

operation 'webauthn' (6 actions):
- register-options          POST  -> retorna challenge + options
- register-verify           POST  -> valida attestation + guarda credential
- login-options             POST  -> retorna challenge + allowCredentials
- login-verify              POST  -> valida assertion + emite JWT
- list-credentials          GET   -> lista credentials del user
- delete-credential         POST  -> elimina un credential

operation 'login' (extensiones):
- verify-password           POST  -> NUEVA  paso 2a tras start con password
- verify-totp               POST  -> NUEVA  paso 3 si MFA configurado
- ...existing del plan 01

operation 'verify' (sin cambios respecto al plan 01)
operation 'session' (sin cambios)
```

## Estructura de carpetas (delta)

```text
serverless/lambda/services/auth/core/
- controllers/
  - mfa/
    - __init__.py
    - setup_totp.py            (SetupTotp(BaseController))
    - confirm_totp.py
    - setup_email_code.py
    - set_preferred.py
    - disable.py
    - list.py                  (List)
    - recovery_codes_generate.py
    - recovery_codes_consume.py
  - webauthn/
    - __init__.py
    - register_options.py
    - register_verify.py
    - login_options.py
    - login_verify.py
    - list_credentials.py
    - delete_credential.py
  - login/                     (extension)
    - verify_password.py       (NUEVO)
    - verify_totp.py           (NUEVO)
- services/
  - totp_service.py            (NUEVO)
  - webauthn_service.py        (NUEVO)
  - recovery_codes_service.py  (NUEVO)
  - challenge_service.py       (NUEVO  CRUD DDB webauthn-challenges)
  - mfa_method_service.py      (NUEVO  CRUD auth_mfa_methods)
  - (existentes del plan 01)
- models/
  - mfa.py                     (NUEVO  Pydantic in schemas)
  - webauthn.py                (NUEVO)
```

## Patron de un controller MFA — ejemplo `mfa.setup-totp`

```python
"""mfa.setup-totp  genera secret + QR.

Requiere: access JWT valido (header Authorization).
Retorna: {secret_b32, otpauth_url, qr_code_svg}. NO persiste todavia
un row confirmado  guarda con confirmed_at=NULL.
"""

from shared.lambda_kit import BaseController
from shared.auth import (
    build_otpauth_url,
    encrypt_envelope,
    generate_totp_secret_b32,
    qr_code_svg,
)
from shared.observability import logger, metrics

from ...services.audit_service import AuditService
from ...services.auth_service import require_active_user
from ...services.mfa_method_service import MfaMethodService
from ...settings.config import app_config


class SetupTotp(BaseController):
    def preload(self):
        return {'is_valid': True, 'data': {}, 'code': 0}

    def validate(self):
        user = require_active_user(
            self.data['_meta'].get('authorization'),
            config=app_config,
        )
        from shared.rate_limit import check_or_raise
        check_or_raise(
            ip=self.data['_meta']['ip'],
            endpoint='/auth#mfa.setup-totp',
            key_override=str(user.id),
        )
        self.context = {'user': user}
        return {'is_valid': True, 'data': {}, 'code': 0}

    def execute(self):
        user = self.context['user']
        mfa_svc = MfaMethodService(app_config)
        audit = AuditService(app_config)

        secret_b32 = generate_totp_secret_b32()
        envelope = encrypt_envelope(
            plaintext=secret_b32.encode('utf-8'),
            kms_key_id=app_config.kms_totp_key_id,
            encryption_context={
                'user_id': str(user.id),
                'purpose': 'totp',
            },
        )
        mfa_svc.upsert_pending_totp(
            user_id=user.id,
            ciphertext=envelope['ciphertext'],
            nonce=envelope['nonce'],
            data_key_ciphertext=envelope['data_key_ciphertext'],
        )

        otpauth_url = build_otpauth_url(
            secret_b32=secret_b32,
            account_email=user.email,
            issuer='the-full-stack.com',
        )
        svg = qr_code_svg(otpauth_url)

        audit.log(event='mfa.setup-totp', success=True, user_id=user.id,
                  ip=self.data['_meta']['ip'])
        metrics.add_metric(name='MfaSetupTotp', unit='Count', value=1)

        return {
            'is_valid': True, 'code': 0,
            'data': {
                'secret_b32': secret_b32,   # mostrar UNA vez; NUNCA logear
                'otpauth_url': otpauth_url,
                'qr_code_svg': svg,
            },
        }
```

## Patron de `webauthn.register-options`

```python
class RegisterOptions(BaseController):
    def execute(self):
        user = self.context['user']
        webauthn_svc = WebauthnService(app_config)
        challenge_svc = ChallengeService(app_config)

        existing = webauthn_svc.list_credential_ids(user_id=user.id)
        options, state = webauthn_svc.build_register_options(
            user_id=user.id, user_name=user.email,
            user_display_name=user.email, existing_credentials=existing,
        )

        challenge_id = new_uuidv7()
        challenge_svc.put_challenge(
            challenge_id=str(challenge_id),
            user_id=str(user.id),
            kind='register',
            state=state,
            ttl_seconds=300,
        )

        return {
            'is_valid': True, 'code': 0,
            'data': {
                'challenge_id': str(challenge_id),
                'options': _options_to_b64_dict(options),
            },
        }
```

El cliente recibe `challenge_id` + `options`. Llama
`navigator.credentials.create({publicKey: options})` y luego POSTea el
attestation_response al endpoint `register-verify` junto con
`challenge_id`. El verify:

1. `GetItem` por `challenge_id` -> obtiene state.
2. Llama `webauthn_svc.verify_registration(state, response)`.
3. `DeleteItem` del challenge.
4. INSERT en `auth_webauthn_credentials`.
5. Retorna `{credential_id, nickname}`.

## Login con MFA — diagrama de flujo

```text
POST /auth operation=login action=start
  body: {email, cf_turnstile, password?}
                 |
                 v
   email no existe?
     si  ->  404 + suggest_register
     no  ->  user activo? (locked -> 423 ACCOUNT_LOCKED)
              |
              v
       password en body?
         no  ->  busca methods (magic-link + email-code + totp + webauthn)
                 emite temp JWT step=1
                 envia magic-link / code via SQS
                 (igual que plan 01)
         si  ->  valida con argon2.verify
                 fail -> 401 INVALID_PASSWORD + incrementa failed_attempts
                 ok   -> user tiene MFA?
                          no  -> emite access+refresh (login terminado)
                          si  -> emite temp JWT step=2
                                 methods = [totp, webauthn]
                                 (continuar con verify-totp / webauthn.login-verify
                                  / mfa.recovery-codes-consume)
                                 |
                                 v
                 emite access+refresh
                 marca last_used_at en el method usado
```

## Que toca cada nuevo service

| Service | Responsabilidad |
|---------|-----------------|
| `MfaMethodService` | CRUD `auth_mfa_methods`: list, upsert_pending_totp, confirm, set_preferred, disable, get_active_methods |
| `TotpService` | wrapper de `shared.auth.totp` + decrypt del secret en cada verify |
| `WebauthnService` | wrapper de `shared.auth.webauthn` + DB ops (`auth_webauthn_credentials`) |
| `ChallengeService` | CRUD DDB `webauthn-challenges`: put, get_and_consume (transactional Get+Delete) |
| `RecoveryCodesService` | gen + hash + persist (INSERT 10 rows) + consume_one_with_lock |

## EventModel  registrar las 14 actions nuevas + 2 de login

```python
# core/models/event.py  extension
EVENT_MODEL = build_event_model({
    'register': {...},   # del plan 01
    'login': {
        'start': LoginStartIn,
        'verify-magic-link': LoginVerifyMagicLinkIn,
        'verify-code': LoginVerifyCodeIn,
        'verify-password': LoginVerifyPasswordIn,    # NUEVO
        'verify-totp': LoginVerifyTotpIn,            # NUEVO
    },
    'verify': {...},     # del plan 01
    'session': {...},    # del plan 01
    'mfa': {
        'setup-totp': MfaSetupTotpIn,
        'confirm-totp': MfaConfirmTotpIn,
        'setup-email-code': MfaSetupEmailCodeIn,
        'set-preferred': MfaSetPreferredIn,
        'disable': MfaDisableIn,
        'list': MfaListIn,
        'recovery-codes-generate': MfaRecoveryCodesGenerateIn,
        'recovery-codes-consume': MfaRecoveryCodesConsumeIn,
    },
    'webauthn': {
        'register-options': WebauthnRegisterOptionsIn,
        'register-verify': WebauthnRegisterVerifyIn,
        'login-options': WebauthnLoginOptionsIn,
        'login-verify': WebauthnLoginVerifyIn,
        'list-credentials': WebauthnListCredentialsIn,
        'delete-credential': WebauthnDeleteCredentialIn,
    },
})
```

## Pydantic schemas — ejemplos

```python
# models/mfa.py
class MfaConfirmTotpIn(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r'^\d{6}$')
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}


class MfaRecoveryCodesConsumeIn(BaseModel):
    temp_token: str = Field(min_length=20)
    code: str = Field(min_length=10, max_length=10,
                       pattern=r'^[A-HJ-NP-Z2-9]{10}$')
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}


# models/webauthn.py
class WebauthnRegisterVerifyIn(BaseModel):
    challenge_id: UUID
    response: dict       # raw fido2 client response
    nickname: str | None = Field(default=None, max_length=64)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}


# models/login.py  extension
class LoginVerifyPasswordIn(BaseModel):
    temp_token: str = Field(min_length=20)
    password: str = Field(min_length=12, max_length=256)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}
```

## Manejo de errores

| Codigo | Significado |
|--------|-------------|
| `MFA_NOT_CONFIGURED` | El user no tiene metodos MFA y intenta `set-preferred` o similar |
| `INVALID_TOTP_CODE` | code TOTP no matchea el secret |
| `MUST_KEEP_ONE_METHOD` | el `disable` dejaria al user sin metodos MFA |
| `MUST_KEEP_ONE_CREDENTIAL` | el `webauthn.delete-credential` dejaria al user con 0 passkeys habiendo otros metodos dependientes |
| `RECOVERY_CODE_CONSUMED` | code ya usado |
| `RECOVERY_CODE_INVALID` | code no matchea (incremento de attempts) |
| `WEBAUTHN_CHALLENGE_NOT_FOUND` | challenge_id no esta en DDB o expiro |
| `WEBAUTHN_CLONE_DETECTED` | sign_count <= stored |
| `WEBAUTHN_RP_ID_MISMATCH` | origin del request no coincide con WEBAUTHN_ALLOWED_ORIGINS |
| `INVALID_PASSWORD` | password no matchea (login.verify-password) |

## Auth helper — `require_active_user`

Nuevo helper en `core/services/auth_service.py`:

```python
def require_active_user(
    authorization_header: str | None,
    *,
    config: AppConfig,
) -> AuthUser:
    """Extrae access JWT del header 'Bearer <X>', valida + verifica
    blacklist + carga user de Neon. Levanta ApplicationError si falla."""
    if not authorization_header or not authorization_header.startswith('Bearer '):
        raise ApplicationError('MISSING_AUTHORIZATION', code=4010)
    raw = authorization_header.removeprefix('Bearer ')

    claims = verify_jwt(raw, secret=config.jwt_secret, expected_typ='access')
    if BlacklistService(config).is_revoked(jti=claims.jti):
        raise JwtRevokedError('TOKEN_BLACKLISTED', code=4011)

    with db_session() as session:
        user = session.get(AuthUser, claims.sub)
        if user is None or user.status != AuthUserStatus.ACTIVE:
            raise ApplicationError('USER_NOT_ACTIVE', code=4012)
    return user
```

El `Authorization` header viaja en `data['_meta']['authorization']` —
se inyecta en `http_handler` desde el evento API GW (el repo ya
inyecta `_meta`; verificar si el header `Authorization` ya esta en
extract_request; si no, agregar la inyeccion como pequeno commit en
`shared.lambda_kit.http_dispatch`).
