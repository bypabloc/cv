"""
Given un response REAL del browser (campos binarios como strings base64url,
    el formato `RegistrationResponseJSON` del spec WebAuthn),
When se parsea con `RegistrationResponse.from_dict` (lo que hace
    `verify_registration` del backend),
Then NO lanza `TypeError: string argument without an encoding` — porque el
    modulo activa `fido2.features.webauthn_json_mapping` al importarse.

Regresion guard del fix backend: fido2 1.x trae ese mapping DESACTIVADO por
defecto y entonces `from_dict` espera bytes, no base64url. Sin el flag, NINGUN
register/login de passkey real (cualquier browser) valida -> 400
WEBAUTHN_REGISTRATION_FAILED. Este test importa el modulo (que prende el flag)
y parsea un response de browser real para que el `from_dict` NO regrese a
esperar bytes.
"""

from __future__ import annotations

from fido2.features import webauthn_json_mapping
from fido2.webauthn import RegistrationResponse

# Importar el modulo del backend DEBE dejar el JSON mapping activo (lo prende
# a nivel de import, idempotente). No se usa ningun simbolo: el efecto es el
# `webauthn_json_mapping.enabled = True` del top del modulo.
import shared.auth.webauthn  # noqa: F401


# `id`/`rawId`/`attestationObject`/`clientDataJSON` como strings base64url:
# EXACTAMENTE el shape que emite el browser (capturado de un ceremony real con
# el Virtual Authenticator de Chrome en el E2E del admin).
_BROWSER_RESPONSE = {
    'id': 'e_-g4peqKta-c40l5I8gVAwL5ddpsfrbhY82_aEDYhM',
    'rawId': 'e_-g4peqKta-c40l5I8gVAwL5ddpsfrbhY82_aEDYhM',
    'response': {
        'attestationObject': (
            'o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YVikPDZS3bX2KPoqRKtt7amwxzYbvz'
            'Z5fXYIgF9nS95y-QpFAAAAAQECAwQFBgcIAQIDBAUGBwgAIHv_oOKXqirWvnONJeSP'
            'IFQMC-XXabH624WPNv2hA2ITpQECAyYgASFYILiDlh-oJ5WLAK8gO9PeD6ogmjs8z1'
            '59KmdyhdX0gB4vIlggDEWjTgsBERbQLGVEra16UhxREvc67RcUO5KD1AgjGr4'
        ),
        'clientDataJSON': (
            'eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmdlIjoibVc4TklRRjM4cE'
            'hadnMyeFZ1Ty1UaDVrRXdWMnNoeWtmT25raEtFNFhaMCIsIm9yaWdpbiI6Imh0dHBz'
            'Oi8vYWRtaW4ucG9ydGZvbGlvLmRldi50aGUtZnVsbC1zdGFjay5jb20iLCJjcm9zc0'
            '9yaWdpbiI6ZmFsc2V9'
        ),
        'transports': ['internal'],
    },
    'type': 'public-key',
    'clientExtensionResults': {},
}


def test_webauthn_json_mapping_enabled_after_import() -> None:
    """Importar shared.auth.webauthn deja el JSON mapping de fido2 activo."""
    # Assert: el flag de proceso quedo prendido (lo prende el modulo al import).
    assert webauthn_json_mapping.enabled is True


def test_from_dict_parses_browser_base64url_response() -> None:
    """from_dict decodifica un response del browser (base64url) sin TypeError.

    Con el JSON mapping APAGADO esto lanzaria
    `TypeError: string argument without an encoding` al castear el `id` string
    a bytes (la causa raiz del 400 WEBAUTHN_REGISTRATION_FAILED).
    """
    # Act: parsea el response tal como llega del browser.
    parsed = RegistrationResponse.from_dict(_BROWSER_RESPONSE)

    # Assert: el `id` se decodifico de base64url a los 32 bytes del credential.
    assert isinstance(parsed.id, bytes)
    assert len(parsed.id) == 32
    assert parsed.response.attestation_object.fmt == 'none'
