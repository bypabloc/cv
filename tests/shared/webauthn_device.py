"""Authenticator WebAuthn de software para los E2E de API (sin browser).

Encapsula `soft_webauthn.SoftWebauthnDevice` para firmar los ceremonies de
register y login de un passkey contra el backend REAL (Lambda `auth`), de
forma DETERMINISTA — sin el Virtual Authenticator del browser (CDP es flaky)
ni la propagacion de Cloudflare.

Por que la subclase `_UvDevice`: el backend pide `user_verification=REQUIRED`
en el login; el `SoftWebauthnDevice.get()` de soft-webauthn 0.1.4 hardcodea
`flags=0x01` (solo User-Present), asi que fido2 rechaza con "User verification
required, but user verified flag not set". La subclase firma con `flags=0x05`
(UP|UV) para que la assertion incluya el flag UV (y la firma cubra ese flag).

Conversion: el backend emite/espera los campos binarios como base64url JSON
(spec WebAuthn); `SoftWebauthnDevice` trabaja con bytes (formato navegador).
Estos helpers convierten en ambos sentidos.
"""

from __future__ import annotations

import base64
from struct import pack
from typing import Any

from soft_webauthn import SoftWebauthnDevice


def b64url_to_bytes(value: str) -> bytes:
    """base64url string -> bytes (tolera padding ausente)."""
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


def bytes_to_b64url(value: bytes) -> str:
    """bytes -> base64url string sin padding (formato del spec WebAuthn)."""
    return base64.urlsafe_b64encode(value).decode('ascii').rstrip('=')


# Flags del authenticatorData: bit0 UP (User Present) + bit2 UV (User
# Verified). El backend exige UV en el login (userVerification=REQUIRED).
_FLAGS_UP_UV = b'\x05'


class _UvDevice(SoftWebauthnDevice):
    """`SoftWebauthnDevice` que firma el login con el flag UV (User Verified).

    Sobreescribe `get` para usar `flags=0x05` (UP|UV) en vez del `0x01` que
    hardcodea soft-webauthn 0.1.4 — sin esto el backend (fido2,
    userVerification=REQUIRED) rechaza la assertion.
    """

    def get(self, options: dict[str, Any], origin: str) -> dict[str, Any]:
        from hashlib import sha256
        import json

        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec

        pub = options['publicKey']
        if self.rp_id != pub['rpId']:
            raise ValueError('Requested rpID does not match current credential')

        self.sign_count += 1
        client_data = json.dumps(
            {
                'type': 'webauthn.get',
                'challenge': bytes_to_b64url(pub['challenge']),
                'origin': origin,
            },
        ).encode('utf-8')
        client_data_hash = sha256(client_data).digest()
        rp_id_hash = sha256(self.rp_id.encode('ascii')).digest()
        authenticator_data = (
            rp_id_hash + _FLAGS_UP_UV + pack('>I', self.sign_count)
        )
        signature = self.private_key.sign(
            authenticator_data + client_data_hash,
            ec.ECDSA(hashes.SHA256()),
        )
        return {
            'id': base64.urlsafe_b64encode(self.credential_id),
            'rawId': self.credential_id,
            'response': {
                'authenticatorData': authenticator_data,
                'clientDataJSON': client_data,
                'signature': signature,
                'userHandle': self.user_handle,
            },
            'type': 'public-key',
        }


class SoftPasskey:
    """Un passkey de software: registra y autentica contra el backend `auth`.

    `origin` es el origin del RP (el admin desplegado), que debe estar en
    `WEBAUTHN_ALLOWED_ORIGINS` del Lambda. El mismo objeto conserva la
    credential entre `register` y `login` (resident key).
    """

    def __init__(self, origin: str) -> None:
        self._origin = origin
        self._device = _UvDevice()

    def register_response(self, options: dict[str, Any]) -> dict[str, Any]:
        """Firma la attestation de `register-options`. Devuelve el response JSON.

        `options` es el `{publicKey: {...b64url...}}` que devuelve el backend.
        """
        pub = options['publicKey']
        create_opts = {
            'publicKey': {
                **pub,
                'challenge': b64url_to_bytes(pub['challenge']),
                'user': {
                    **pub['user'],
                    'id': b64url_to_bytes(pub['user']['id']),
                },
            },
        }
        att = self._device.create(create_opts, self._origin)
        return {
            'id': bytes_to_b64url(att['rawId']),
            'rawId': bytes_to_b64url(att['rawId']),
            'type': att['type'],
            'response': {
                'attestationObject': bytes_to_b64url(
                    att['response']['attestationObject'],
                ),
                'clientDataJSON': bytes_to_b64url(
                    att['response']['clientDataJSON'],
                ),
            },
        }

    def login_response(self, options: dict[str, Any]) -> dict[str, Any]:
        """Firma la assertion de `login-options` (con flag UV). Response JSON."""
        pub = options['publicKey']
        get_opts = {
            'publicKey': {
                **pub,
                'challenge': b64url_to_bytes(pub['challenge']),
                'allowCredentials': [
                    {**c, 'id': b64url_to_bytes(c['id'])}
                    for c in pub.get('allowCredentials', [])
                ],
            },
        }
        asrt = self._device.get(get_opts, self._origin)
        uh = asrt['response'].get('userHandle')
        return {
            'id': bytes_to_b64url(asrt['rawId']),
            'rawId': bytes_to_b64url(asrt['rawId']),
            'type': asrt['type'],
            'response': {
                'authenticatorData': bytes_to_b64url(
                    asrt['response']['authenticatorData'],
                ),
                'clientDataJSON': bytes_to_b64url(
                    asrt['response']['clientDataJSON'],
                ),
                'signature': bytes_to_b64url(asrt['response']['signature']),
                'userHandle': bytes_to_b64url(uh) if uh else None,
            },
        }
