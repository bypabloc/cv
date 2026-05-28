# 03. Shared.auth extension — TOTP + WebAuthn + recovery codes + envelope encryption

## Que se agrega al subpackage

```text
serverless/lambda/shared/auth/
├── ... (archivos del plan 01)
├── totp.py             # NUEVO: pyotp wrappers
├── webauthn.py         # NUEVO: fido2 wrappers
├── recovery_codes.py   # NUEVO: generate_recovery_codes + hash + compare
└── encryption.py       # NUEVO: envelope encryption KMS + AES-256-GCM
```

## Update al `pyproject.toml`

```toml
[project]
dependencies = [
    "pyjwt>=2.9,<3.0",
    "argon2-cffi>=23.1,<24.0",
    "pyotp>=2.9,<3.0",               # NUEVO
    "python-fido2>=1.1,<2.0",        # NUEVO
    "cryptography>=42.0,<43.0",       # NUEVO (para AES-GCM)
]
```

## Update al `__init__.py` (re-exports)

```python
from .encryption import (
    EnvelopeEncryptionError,
    decrypt_envelope,
    encrypt_envelope,
)
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
    qr_code_svg,
    verify_totp_code,
)
from .webauthn import (
    WebauthnError,
    WebauthnVerifyError,
    build_register_options,
    build_login_options,
    verify_registration,
    verify_authentication,
)

__all__ = [
    # ... existentes
    'EnvelopeEncryptionError',
    'decrypt_envelope',
    'encrypt_envelope',
    'RECOVERY_CODE_ALPHABET',
    'RECOVERY_CODE_LENGTH',
    'compare_recovery_code',
    'generate_recovery_codes',
    'hash_recovery_code',
    'TotpError',
    'build_otpauth_url',
    'generate_totp_secret_b32',
    'qr_code_svg',
    'verify_totp_code',
    'WebauthnError',
    'WebauthnVerifyError',
    'build_register_options',
    'build_login_options',
    'verify_registration',
    'verify_authentication',
]
```

## `encryption.py` — envelope encryption con KMS DataKey

```python
"""Envelope encryption usando AWS KMS GenerateDataKey + AES-256-GCM.

NO usar para mas de 2^32 mensajes con la misma DataKey (limite GCM).
Para TOTP, una DataKey por user => safe.
"""

import boto3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from shared.core import ApplicationError


class EnvelopeEncryptionError(ApplicationError): ...


_KMS = boto3.client('kms')


def encrypt_envelope(
    *, plaintext: bytes, kms_key_id: str,
    encryption_context: dict[str, str] | None = None,
) -> dict:
    """Genera DataKey y cifra plaintext con AES-256-GCM.

    Retorna {ciphertext, nonce, data_key_ciphertext}.
    """
    resp = _KMS.generate_data_key(
        KeyId=kms_key_id, KeySpec='AES_256',
        EncryptionContext=encryption_context or {},
    )
    plain_dk = resp['Plaintext']
    ct_dk = resp['CiphertextBlob']

    nonce = os.urandom(12)
    cipher = AESGCM(plain_dk)
    aad = b''  # opcional; mantener vacio o derivar del contexto
    ciphertext = cipher.encrypt(nonce, plaintext, aad)

    # Zero out la key plana en memoria (best-effort)
    plain_dk = b'\x00' * len(plain_dk)

    return {
        'ciphertext': ciphertext,
        'nonce': nonce,
        'data_key_ciphertext': ct_dk,
    }


def decrypt_envelope(
    *, ciphertext: bytes, nonce: bytes, data_key_ciphertext: bytes,
    encryption_context: dict[str, str] | None = None,
) -> bytes:
    resp = _KMS.decrypt(
        CiphertextBlob=data_key_ciphertext,
        EncryptionContext=encryption_context or {},
    )
    plain_dk = resp['Plaintext']
    cipher = AESGCM(plain_dk)
    plaintext = cipher.decrypt(nonce, ciphertext, b'')
    plain_dk = b'\x00' * len(plain_dk)
    return plaintext
```

> NOTA importante: el cliente boto3 KMS debe venir de `shared.aws`
> (catalogo de portadores). En la version implementada,
> `encryption.py` importa `from shared.aws import kms` o agrega un
> wrapper en `shared.aws` que expone `generate_data_key` /
> `decrypt`. **Update al catalogo de portadores** (rule
> `lambda-shared-imports.md`) sera parte de este plan.

## `totp.py` — pyotp wrappers

```python
import pyotp


def generate_totp_secret_b32() -> str:
    """20 bytes random codificados en base32 (160 bits, RFC 6238)."""
    return pyotp.random_base32()  # 32 chars base32 = 160 bits


def build_otpauth_url(
    *, secret_b32: str, account_email: str, issuer: str = 'the-full-stack.com',
) -> str:
    """RFC 6238 URL para QR codes. Compatible Google Authenticator/Authy/1Password."""
    return pyotp.TOTP(secret_b32).provisioning_uri(
        name=account_email, issuer_name=issuer)


def qr_code_svg(otpauth_url: str) -> str:
    """SVG inline del QR (sin dependencias extras: usar `qrcode[pil]` o
    derivar matriz manual). Decision: usar `segno` (~7KB pure-python)."""
    import segno
    qr = segno.make(otpauth_url, error='M')
    buf = io.StringIO()
    qr.save(buf, kind='svg', xmldecl=False, omitsize=True, scale=4)
    return buf.getvalue()


def verify_totp_code(*, secret_b32: str, code: str, valid_window: int = 1) -> bool:
    """valid_window=1 acepta el code actual + el anterior + el siguiente
    (cubre clock drift hasta 30s)."""
    return pyotp.TOTP(secret_b32).verify(code, valid_window=valid_window)


class TotpError(ApplicationError): ...
```

Decision: la libreria `segno` se agrega como dep ADICIONAL a
`shared.auth` (es trivial, 0 deps externas). Alternativa: pre-generar
el SVG en el frontend desde el `otpauth_url` con `qrcode-svg` JS.
Preferimos backend para no depender del frontend.

## `webauthn.py` — fido2 wrappers

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

| Archivo | Escenario |
|---------|-----------|
| `test_totp_secret_b32_length.py` | secret > 16 chars, todos en alfabeto base32 |
| `test_totp_otpauth_url_format.py` | URL matchea `otpauth://totp/...` con issuer y email |
| `test_totp_verify_correct.py` | code generado por pyotp.TOTP(secret).now() -> True |
| `test_totp_verify_wrong.py` | code aleatorio -> False |
| `test_totp_verify_drift_acceptable.py` | code de hace 30s -> True (valid_window=1) |
| `test_totp_verify_drift_too_old.py` | code de hace 90s -> False |
| `test_qr_svg_renders.py` | output contiene `<svg`, `</svg>`, sin errores |
| `test_webauthn_register_options.py` | options dict tiene `challenge`, `rp.id`, `user.id` |
| `test_webauthn_register_verify_ok.py` | con fixture de fido2 stubs -> verifica + retorna credential_id |
| `test_webauthn_login_options.py` | retorna allowCredentials con stored IDs |
| `test_webauthn_login_verify_ok.py` | assertion valida -> new_sign_count > old |
| `test_webauthn_login_verify_sign_count_clone.py` | new <= old -> raises WebauthnVerifyError |
| `test_recovery_codes_generate_10.py` | exactly 10 codes, todos length=10, en alfabeto |
| `test_recovery_codes_hash_compare.py` | round-trip |
| `test_envelope_encrypt_decrypt_roundtrip.py` | (con KMS local-stack o moto) round-trip exitoso |
| `test_envelope_decrypt_with_wrong_context_fails.py` | mismatch encryption_context -> KMS levanta error |
| `test_envelope_decrypt_corrupted_ciphertext.py` | flipear 1 byte del ciphertext -> AESGCM levanta InvalidTag |

## Update al catalogo de portadores

En `.claude/rules/lambda-shared-imports.md` agregar (al cierre del
plan):

| Paquete externo | Portador shared | Como se importa |
|-----------------|-----------------|------------------|
| `pyotp` | `shared.auth` | `from shared.auth import generate_totp_secret_b32, verify_totp_code, build_otpauth_url, qr_code_svg` |
| `python-fido2` | `shared.auth` | `from shared.auth import build_register_options, verify_registration, build_login_options, verify_authentication` |
| `cryptography` (AESGCM) | `shared.auth` | `from shared.auth import encrypt_envelope, decrypt_envelope` |
| `segno` (QR svg) | `shared.auth` | re-exportada via `qr_code_svg` solamente |
| `boto3.client('kms')` | `shared.aws` | wrapper `kms_generate_data_key`, `kms_decrypt` agregados a `shared.aws/__init__.py` |
