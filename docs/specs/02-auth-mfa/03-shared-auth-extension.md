# 03. Shared.auth extension — TOTP + WebAuthn + recovery codes (KMS via shared.aws)

> El cifrado del TOTP secret NO vive en `shared.auth/encryption.py`:
> se hace con `kms:Encrypt` / `kms:Decrypt` directos via los wrappers
> `kms_encrypt` / `kms_decrypt` de `shared.aws.kms` (CMK directa,
> sin envelope encryption — decision 1 del plan).

## Que se agrega al subpackage

```text
serverless/lambda/shared/auth/
├── ... (archivos del plan 01)
├── totp.py             # NUEVO: pyotp wrappers
├── webauthn.py         # NUEVO: fido2 wrappers
└── recovery_codes.py   # NUEVO: generate_recovery_codes + hash + compare
```

Y, separado, en `shared.aws/`:

```text
serverless/lambda/shared/aws/
├── ... (archivos existentes)
└── kms.py              # NUEVO: kms_encrypt + kms_decrypt
```

## Update al `pyproject.toml` (shared.auth)

```toml
[project]
dependencies = [
    "pyjwt>=2.9,<3.0",
    "argon2-cffi>=23.1,<24.0",
    "pyotp>=2.9,<3.0",               # NUEVO
    "python-fido2>=1.1,<2.0",        # NUEVO
    # NO `cryptography`: el cifrado lo hace KMS server-side (CMK directa).
    # NO `segno`: el QR lo renderiza el frontend desde el otpauth_url.
]
```

## Update al `shared/auth/__init__.py` (re-exports)

```python
from .recovery_codes import (
    RECOVERY_CODE_ALPHABET,
    RECOVERY_CODE_LENGTH,
    compare_recovery_code,
    generate_recovery_codes,
    hash_recovery_code,
)
from .totp import (
    TotpError,
    build_otpauth_url,
    generate_totp_secret_b32,
    verify_totp_code,
)
from .webauthn import (
    WebauthnError,
    WebauthnVerifyError,
    build_login_options,
    build_register_options,
    verify_authentication,
    verify_registration,
)

__all__ = [
    # ... existentes del plan 01
    'RECOVERY_CODE_ALPHABET',
    'RECOVERY_CODE_LENGTH',
    'compare_recovery_code',
    'generate_recovery_codes',
    'hash_recovery_code',
    'TotpError',
    'build_otpauth_url',
    'generate_totp_secret_b32',
    'verify_totp_code',
    'WebauthnError',
    'WebauthnVerifyError',
    'build_login_options',
    'build_register_options',
    'verify_authentication',
    'verify_registration',
]
```

## Update al `shared/aws/__init__.py` (re-exports)

```python
from .kms import KmsError, kms_decrypt, kms_encrypt

__all__ = [
    # ... existentes (DynamoDB, SES, SSM, etc.)
    'KmsError',
    'kms_decrypt',
    'kms_encrypt',
]
```

## `shared/aws/kms.py` — wrappers KMS Encrypt/Decrypt directos

```python
"""AWS KMS Encrypt/Decrypt con CMK directa.

Para secretos <= 4 KB (limite de kms:Encrypt). EncryptionContext es
obligatorio para audit + binding criptografico al user_id.

NO envelope encryption — el secret TOTP es 20 bytes, entra holgado.
"""

import boto3

from shared.core import ApplicationError


class KmsError(ApplicationError): ...


_KMS = boto3.client('kms')


def kms_encrypt(
    *,
    plaintext: bytes,
    key_id: str,
    encryption_context: dict[str, str],
) -> bytes:
    """Cifra plaintext con la CMK key_id. Retorna ciphertext (BYTEA).

    encryption_context queda bindeado al ciphertext; el decrypt debe
    pasar el MISMO encryption_context o falla con `InvalidCiphertextException`.
    Convention: {'user_id': str(user.id), 'purpose': 'totp'}.
    """
    try:
        resp = _KMS.encrypt(
            KeyId=key_id,
            Plaintext=plaintext,
            EncryptionContext=encryption_context,
        )
    except _KMS.exceptions.ClientError as exc:
        raise KmsError(f'kms_encrypt failed: {exc.response["Error"]["Code"]}') from exc
    return resp['CiphertextBlob']


def kms_decrypt(
    *,
    ciphertext: bytes,
    encryption_context: dict[str, str],
    key_id: str | None = None,
) -> bytes:
    """Descifra ciphertext. encryption_context DEBE matchear el del encrypt.

    El `key_id` es opcional (KMS lo deriva del ciphertext); pasarlo
    explicitamente cuando se sabe es defensa en profundidad.
    """
    kwargs = {
        'CiphertextBlob': ciphertext,
        'EncryptionContext': encryption_context,
    }
    if key_id is not None:
        kwargs['KeyId'] = key_id
    try:
        resp = _KMS.decrypt(**kwargs)
    except _KMS.exceptions.ClientError as exc:
        raise KmsError(f'kms_decrypt failed: {exc.response["Error"]["Code"]}') from exc
    return resp['Plaintext']
```

> Cache de plaintext: `shared.cache` (TTL 5 min, scope cold-start del
> Lambda) sobre `(ciphertext_hash, user_id)` para evitar martillar
> KMS en cada `login.verify-totp` consecutivo. La cache se purga al
> rotar el secret TOTP (re-`setup-totp`).
>
> **Update al catalogo de portadores** (rule
> `.claude/rules/lambda-shared-imports.md`): `boto3.client('kms')`
> -> portador `shared.aws`, exportado como `kms_encrypt` /
> `kms_decrypt`. La actualizacion se hace en PR 2 (commit 2.2), NO
> en PR 1 — para evitar incoherencia entre catalogo y codigo
> publicado.

## `totp.py` — pyotp wrappers

```python
import pyotp

from shared.core import ApplicationError


class TotpError(ApplicationError): ...


def generate_totp_secret_b32() -> str:
    """20 bytes random codificados en base32 (160 bits, RFC 6238)."""
    return pyotp.random_base32()  # 32 chars base32 = 160 bits


def build_otpauth_url(
    *, secret_b32: str, account_email: str, issuer: str = 'the-full-stack.com',
) -> str:
    """RFC 6238 URL para QR codes. Compatible Google Authenticator/Authy/1Password."""
    return pyotp.TOTP(secret_b32).provisioning_uri(
        name=account_email, issuer_name=issuer)


def verify_totp_code(*, secret_b32: str, code: str, valid_window: int = 1) -> bool:
    """valid_window=1 acepta el code actual + el anterior + el siguiente
    (cubre clock drift hasta 30s)."""
    return pyotp.TOTP(secret_b32).verify(code, valid_window=valid_window)
```

> El QR lo renderiza el frontend desde el `otpauth_url` (decision 8):
> el cliente usa `qrcode` JS (~5KB gzipped) y muestra el QR inline.
> Razon: evita una dep mas (`segno`) en el Lambda, ahorra ~3-5 KB
> de response y mejora el cold start.

## `webauthn.py` — fido2 wrappers

> **PRE-IMPLEMENTACION OBLIGATORIA**: spike de 30 min validando la API
> actual de `python-fido2` 1.x (decision 4 del README). Verificar:
>
> - shape exacto de `Fido2Server.register_begin` / `register_complete` /
>   `authenticate_begin` / `authenticate_complete` (el `state` retornado
>   suele ser un `dict` JSON-serializable, NO `bytes` — guardarlo en DDB
>   como `Map` o `json.dumps`).
> - import paths reales de `AttestedCredentialData`, `PublicKey`,
>   `AuthenticatorData`.
> - signatura de `register_complete` (acepta `state` + `response` o
>   acepta otros parametros adicionales).
>
> El codigo de abajo es PSEUDOCODE que refleja la intencion; la
> implementacion final se ajusta tras el spike. Si la firma difiere
> significativamente, este archivo se actualiza ANTES del PR 2.

```python
from fido2.webauthn import (
    AttestationConveyancePreference, AuthenticatorSelectionCriteria,
    AuthenticatorAttachment, ResidentKeyRequirement,
    PublicKeyCredentialRpEntity, PublicKeyCredentialUserEntity,
    UserVerificationRequirement, PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
)
from fido2.server import Fido2Server


class WebauthnError(ApplicationError): ...
class WebauthnVerifyError(WebauthnError): ...


def _make_server(*, rp_id: str, rp_name: str, expected_origins: list[str]) -> Fido2Server:
    return Fido2Server(
        PublicKeyCredentialRpEntity(id=rp_id, name=rp_name),
        verify_origin=lambda origin: origin in expected_origins,
    )


def build_register_options(
    *, rp_id: str, rp_name: str, expected_origins: list[str],
    user_id: bytes, user_name: str, user_display_name: str,
    existing_credentials: list[bytes],
) -> tuple[dict, bytes]:
    """Retorna (options_dict_b64, state) — state se guarda en DDB."""
    server = _make_server(rp_id=rp_id, rp_name=rp_name,
                          expected_origins=expected_origins)
    user = PublicKeyCredentialUserEntity(
        id=user_id, name=user_name, display_name=user_display_name)
    auth_selection = AuthenticatorSelectionCriteria(
        authenticator_attachment=None,  # platform o cross-platform
        resident_key=ResidentKeyRequirement.PREFERRED,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    exclude = [
        PublicKeyCredentialDescriptor(type=PublicKeyCredentialType.PUBLIC_KEY,
                                       id=cred_id)
        for cred_id in existing_credentials
    ]
    options, state = server.register_begin(
        user=user, credentials=exclude,
        user_verification=UserVerificationRequirement.PREFERRED,
        authenticator_attachment=None,
    )
    return options, state  # state = bytes, se persiste en DDB


def verify_registration(
    *, rp_id: str, rp_name: str, expected_origins: list[str],
    state: bytes, response: dict,
) -> dict:
    """Retorna {credential_id, public_key, sign_count, transports, ...}."""
    server = _make_server(rp_id=rp_id, rp_name=rp_name,
                          expected_origins=expected_origins)
    auth_data = server.register_complete(state, response)
    return {
        'credential_id': auth_data.credential_data.credential_id,
        'public_key': auth_data.credential_data.public_key,
        'sign_count': auth_data.counter,
        'aaguid': auth_data.credential_data.aaguid,
        'attestation_format': response.get('fmt', 'none'),
    }


def build_login_options(
    *, rp_id: str, rp_name: str, expected_origins: list[str],
    allowed_credentials: list[bytes],
) -> tuple[dict, bytes]:
    server = _make_server(rp_id=rp_id, rp_name=rp_name,
                          expected_origins=expected_origins)
    creds = [
        PublicKeyCredentialDescriptor(type=PublicKeyCredentialType.PUBLIC_KEY,
                                       id=cred_id)
        for cred_id in allowed_credentials
    ]
    options, state = server.authenticate_begin(
        credentials=creds,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    return options, state


def verify_authentication(
    *, rp_id: str, rp_name: str, expected_origins: list[str],
    state: bytes, response: dict, stored_credentials: list[dict],
) -> dict:
    """stored_credentials = [{'credential_id': bytes, 'public_key': bytes,
       'sign_count': int}]. Retorna {credential_id, new_sign_count}."""
    server = _make_server(rp_id=rp_id, rp_name=rp_name,
                          expected_origins=expected_origins)
    creds = [
        AttestedCredentialData(
            aaguid=b'\x00' * 16,
            credential_id=c['credential_id'],
            public_key=PublicKey.from_bytes(c['public_key']),
        ) for c in stored_credentials
    ]
    auth_data = server.authenticate_complete(state, creds, response)
    return {
        'credential_id': auth_data.credential_id,
        'new_sign_count': auth_data.counter,
    }
```

## `recovery_codes.py`

```python
RECOVERY_CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
RECOVERY_CODE_LENGTH = 10
RECOVERY_CODE_COUNT = 10


def generate_recovery_codes() -> list[str]:
    """10 codes de 10 chars sin O/0/I/1/L. CSPRNG."""
    return [
        ''.join(secrets.choice(RECOVERY_CODE_ALPHABET)
                for _ in range(RECOVERY_CODE_LENGTH))
        for _ in range(RECOVERY_CODE_COUNT)
    ]


def hash_recovery_code(code: str) -> bytes:
    """SHA-256 — codes son 10 chars (espacio 30^10 ~ 5.9x10^14)."""
    return hashlib.sha256(code.encode('utf-8')).digest()


def compare_recovery_code(*, code: str, stored_hash: bytes) -> bool:
    return secrets.compare_digest(hash_recovery_code(code), stored_hash)
```

## Tests unit

Path: `serverless/lambda/shared/tests/unit/shared/auth/`.

Path `shared/auth/`:

| Archivo | Escenario |
|---------|-----------|
| `test_totp_secret_b32_length.py` | secret > 16 chars, todos en alfabeto base32 |
| `test_totp_otpauth_url_format.py` | URL matchea `otpauth://totp/...` con issuer y email |
| `test_totp_verify_correct.py` | code generado por pyotp.TOTP(secret).now() -> True |
| `test_totp_verify_wrong.py` | code aleatorio -> False |
| `test_totp_verify_drift_acceptable.py` | code de hace 30s -> True (valid_window=1) |
| `test_totp_verify_drift_too_old.py` | code de hace 90s -> False |
| `test_webauthn_register_options.py` | options dict tiene `challenge`, `rp.id`, `user.id` |
| `test_webauthn_register_verify_ok.py` | con fixture de fido2 stubs -> verifica + retorna credential_id |
| `test_webauthn_login_options.py` | retorna allowCredentials con stored IDs |
| `test_webauthn_login_verify_ok.py` | assertion valida -> new_sign_count > old |
| `test_webauthn_login_verify_sign_count_clone.py` | new <= old -> raises WebauthnVerifyError |
| `test_recovery_codes_generate_10.py` | exactly 10 codes, todos length=10, en alfabeto |
| `test_recovery_codes_hash_compare.py` | round-trip |

Path `shared/aws/` (KMS):

| Archivo | Escenario |
|---------|-----------|
| `test_kms_encrypt_returns_ciphertext.py` | (moto.mock_aws) encrypt retorna bytes |
| `test_kms_encrypt_decrypt_roundtrip.py` | round-trip con el mismo encryption_context |
| `test_kms_decrypt_wrong_context_fails.py` | mismatch encryption_context -> KmsError |
| `test_kms_decrypt_invalid_ciphertext.py` | ciphertext aleatorio -> KmsError |

## Update al catalogo de portadores

En `.claude/rules/lambda-shared-imports.md` agregar (al cierre del PR 2 —
NO en PR 1, para evitar incoherencia entre catalogo declarativo y codigo
publicado):

| Paquete externo | Portador shared | Como se importa |
|-----------------|-----------------|------------------|
| `pyotp` | `shared.auth` | `from shared.auth import generate_totp_secret_b32, verify_totp_code, build_otpauth_url` |
| `python-fido2` | `shared.auth` | `from shared.auth import build_register_options, verify_registration, build_login_options, verify_authentication` |
| `boto3.client('kms')` | `shared.aws` | wrappers `kms_encrypt`, `kms_decrypt` agregados a `shared.aws/__init__.py` |

NO se agrega `cryptography` (no se usa — CMK directa sustituye AES-GCM
propio). NO se agrega `segno` (el QR lo renderiza el frontend).
