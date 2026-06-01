"""WebAuthn / Passkeys wrappers sobre `python-fido2` (Yubico, 1.x).

Portador unico de `fido2` para el backend (regla
`.claude/rules/lambda-shared-imports.md`). Encapsula `Fido2Server` para
los 4 momentos del ceremony WebAuthn:

- `build_register_options` -> options (JSON browser-ready) + state.
- `verify_registration`     -> credential_id + public_key (CBOR) + ...
- `build_login_options`     -> options + state.
- `verify_authentication`   -> credential_id + new_sign_count (clone check).

`state` es el dict JSON-serializable que devuelve fido2
(`{'challenge': '<b64url>', 'user_verification': '<value>'}`) — se
persiste en DynamoDB (TTL 5 min) entre el `*-options` y el `*-verify`.

`public_key` se serializa a bytes con CBOR (`fido2.cbor.encode`) para
guardar en `auth_webauthn_credentials.public_key`; se reconstruye con
`CoseKey.parse(cbor.decode(...))` al verificar el login.

API de fido2 1.2 validada en el spike del plan (decision 4):
- `Fido2Server(rp, attestation, verify_origin)`.
- `register_begin(user, credentials, resident_key_requirement,
   user_verification) -> (CredentialCreationOptions, state_dict)`.
- `register_complete(state, response_dict) -> AuthenticatorData`.
- `authenticate_begin(credentials, user_verification) ->
   (CredentialRequestOptions, state_dict)`.
- `authenticate_complete(state, credentials, response_dict) ->
   AttestedCredentialData` (la matched; el counter NUEVO se parsea del
   response, fido2 NO valida regresion de sign_count — eso lo hacemos
   aqui = clone detection).
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Any

from fido2 import cbor
from fido2.cose import CoseKey
from fido2.server import Fido2Server
from fido2.utils import websafe_encode
from fido2.webauthn import (
    AttestationConveyancePreference,
    AttestedCredentialData,
    AuthenticationResponse,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialRpEntity,
    PublicKeyCredentialType,
    PublicKeyCredentialUserEntity,
    RegistrationResponse,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from shared.core.exceptions import ApplicationError


class WebauthnError(ApplicationError):
    """Fallo generico en una operacion WebAuthn."""


class WebauthnVerifyError(WebauthnError):
    """La attestation o assertion no valida (signature/challenge/origin)."""


class WebauthnCloneError(WebauthnVerifyError):
    """sign_count regreso (`new <= stored`) — credential potencialmente clonado.

    Lleva `credential_id` para que el service marque el credential
    `disabled_at=now()` (AC-15 / decision 14).
    """

    def __init__(self, message: str, *, credential_id: bytes) -> None:
        super().__init__(message)
        self.credential_id = credential_id


def _to_json(obj: Any) -> Any:
    """Convierte recursivamente las options de fido2 a JSON browser-ready.

    fido2 devuelve bytes (challenge, user.id, credential ids) y enums; el
    browser espera base64url strings y valores de enum. Recorre Mappings,
    listas, bytes y enums.
    """
    if isinstance(obj, bytes):
        return websafe_encode(obj)
    if isinstance(obj, Mapping):
        return {k: _to_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json(v) for v in obj]
    if isinstance(obj, Enum):
        return obj.value
    return obj


def _make_server(
    *,
    rp_id: str,
    rp_name: str,
    expected_origins: list[str],
) -> Fido2Server:
    """Construye un `Fido2Server` con attestation=none + verify_origin allowlist."""
    return Fido2Server(
        PublicKeyCredentialRpEntity(id=rp_id, name=rp_name),
        attestation=AttestationConveyancePreference.NONE,
        verify_origin=lambda origin: origin in expected_origins,
    )


def _descriptors(
    credential_ids: list[bytes],
) -> list[PublicKeyCredentialDescriptor]:
    return [
        PublicKeyCredentialDescriptor(
            type=PublicKeyCredentialType.PUBLIC_KEY,
            id=cred_id,
        )
        for cred_id in credential_ids
    ]


def build_register_options(
    *,
    rp_id: str,
    rp_name: str,
    expected_origins: list[str],
    user_id: bytes,
    user_name: str,
    user_display_name: str,
    existing_credentials: list[bytes],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Retorna `(options_json, state)`. `state` se persiste en DDB.

    `options_json` es el dict JSON browser-ready para
    `navigator.credentials.create({publicKey: options_json.publicKey})`.
    `existing_credentials` se excluyen para evitar registrar 2 veces el
    mismo authenticator.
    """
    server = _make_server(
        rp_id=rp_id,
        rp_name=rp_name,
        expected_origins=expected_origins,
    )
    user = PublicKeyCredentialUserEntity(
        id=user_id,
        name=user_name,
        display_name=user_display_name,
    )
    options, state = server.register_begin(
        user=user,
        credentials=_descriptors(existing_credentials),
        resident_key_requirement=ResidentKeyRequirement.PREFERRED,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    return _to_json(options), state


def verify_registration(
    *,
    rp_id: str,
    rp_name: str,
    expected_origins: list[str],
    state: dict[str, Any],
    response: dict[str, Any],
) -> dict[str, Any]:
    """Valida la attestation. Retorna los datos del credential a persistir.

    `response` es el `PublicKeyCredential` JSON del browser. Retorna
    `{credential_id, public_key, sign_count, aaguid, attestation_format,
    transports}`. `public_key` es CBOR bytes (listo para BYTEA).

    Raises:
        WebauthnVerifyError: si la attestation no valida.
    """
    server = _make_server(
        rp_id=rp_id,
        rp_name=rp_name,
        expected_origins=expected_origins,
    )
    try:
        parsed = RegistrationResponse.from_dict(response)
        auth_data = server.register_complete(state, parsed)
    except Exception as exc:
        raise WebauthnVerifyError(f'registration failed: {exc}') from exc

    cred = auth_data.credential_data
    if cred is None:  # pragma: no cover - fido2 garantiza credential_data
        raise WebauthnVerifyError('registration missing credential data')

    inner = response.get('response', {}) if isinstance(response, dict) else {}
    transports = inner.get('transports')
    attestation_format = parsed.response.attestation_object.fmt or 'none'

    return {
        'credential_id': bytes(cred.credential_id),
        'public_key': cbor.encode(cred.public_key),
        'sign_count': int(auth_data.counter),
        'aaguid': bytes(cred.aaguid) if cred.aaguid else None,
        'attestation_format': attestation_format,
        'transports': transports,
    }


def build_login_options(
    *,
    rp_id: str,
    rp_name: str,
    expected_origins: list[str],
    allowed_credentials: list[bytes],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Retorna `(options_json, state)` para el login ceremony.

    `allowed_credentials` son los credential_id activos del user.
    """
    server = _make_server(
        rp_id=rp_id,
        rp_name=rp_name,
        expected_origins=expected_origins,
    )
    options, state = server.authenticate_begin(
        credentials=_descriptors(allowed_credentials),
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    return _to_json(options), state


def verify_authentication(
    *,
    rp_id: str,
    rp_name: str,
    expected_origins: list[str],
    state: dict[str, Any],
    response: dict[str, Any],
    stored_credentials: list[dict[str, Any]],
) -> dict[str, Any]:
    """Valida la assertion + clone detection. Retorna `{credential_id, new_sign_count}`.

    `stored_credentials = [{'credential_id': bytes, 'public_key': bytes
    (CBOR), 'sign_count': int}]`. fido2 valida signature/challenge/origin;
    AQUI validamos la regresion de sign_count (clone detection): si el
    nuevo `<= stored` y el stored `> 0`, levantamos `WebauthnCloneError`
    (decision 14 / AC-15).

    Raises:
        WebauthnVerifyError: assertion invalida o credential desconocido.
        WebauthnCloneError: sign_count regreso (potencial clon).
    """
    server = _make_server(
        rp_id=rp_id,
        rp_name=rp_name,
        expected_origins=expected_origins,
    )
    creds = [
        AttestedCredentialData.create(
            aaguid=b'\x00' * 16,
            credential_id=c['credential_id'],
            public_key=CoseKey.parse(cbor.decode(c['public_key'])),
        )
        for c in stored_credentials
    ]
    try:
        matched = server.authenticate_complete(state, creds, response)
    except Exception as exc:
        raise WebauthnVerifyError(f'authentication failed: {exc}') from exc

    matched_id = bytes(matched.credential_id)
    new_sign_count = _extract_counter(response)
    stored_count = next(
        (
            int(c['sign_count'])
            for c in stored_credentials
            if c['credential_id'] == matched_id
        ),
        0,
    )
    if stored_count > 0 and new_sign_count <= stored_count:
        raise WebauthnCloneError(
            f'sign_count regression: new={new_sign_count} <= '
            f'stored={stored_count}',
            credential_id=matched_id,
        )

    return {'credential_id': matched_id, 'new_sign_count': new_sign_count}


def _extract_counter(response: dict[str, Any]) -> int:
    """Parsea el `authenticator_data.counter` de la assertion del browser."""
    parsed = AuthenticationResponse.from_dict(response)
    return int(parsed.response.authenticator_data.counter)
