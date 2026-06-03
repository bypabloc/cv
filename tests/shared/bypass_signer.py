"""Firma de tokens de bypass de Turnstile (Ed25519) — lado tests/shared.

ESPEJO de `serverless/lambda/shared/crypto/bypass_token.py` (el verificador
del Lambda) y de `devtools/shared/bypass_token.py` (el firmante del CLI).
Mismo formato de token EXACTO para que un token firmado aca sea verificable
por el backend:

    token = b64url(payload_json) "." b64url(signature)

- `payload_json`: JSON canonico de `{v, iat, exp, jti, stage}` con
  `sort_keys=True` y separadores compactos.
- `signature`: Ed25519 sobre los BYTES ASCII del primer segmento.

`tests/shared` NO puede importar `devtools/shared/bypass_token.py`: ambos
son paquetes top-level `shared` y colisionan en el mismo `sys.path`
(`tests/shared` gana cuando el harness corre con `tests/` al frente). Por
eso este modulo VENDORIZA el firmante. La clave privada NUNCA debe
loguearse ni salir del entorno local (`docker/env/dev-cli/`).
"""

from __future__ import annotations

import base64
import json
import secrets


TOKEN_VERSION = 1
DEFAULT_TTL_SECONDS = 300


def _b64url_encode(raw: bytes) -> str:
    """Codifica bytes a base64 urlsafe SIN padding."""
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


def _b64url_decode(value: str) -> bytes:
    """Decodifica base64 urlsafe SIN padding."""
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign_message(private_key_b64: str, message: bytes) -> bytes:
    """Firma `message` con la clave privada Ed25519 (raw, base64)."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

    private_key = Ed25519PrivateKey.from_private_bytes(
        _b64url_decode(private_key_b64),
    )
    return private_key.sign(message)


def build_payload(
    *,
    stage: str,
    now: int,
    ttl: int = DEFAULT_TTL_SECONDS,
) -> dict[str, object]:
    """Construye el payload `{v, iat, exp, jti, stage}`."""
    return {
        'v': TOKEN_VERSION,
        'iat': now,
        'exp': now + ttl,
        'jti': secrets.token_hex(8),
        'stage': stage,
    }


def sign_bypass_token(
    *,
    stage: str,
    private_key_b64: str,
    now: int,
    ttl: int = DEFAULT_TTL_SECONDS,
) -> str:
    """Emite un token de bypass firmado, verificable por el backend.

    Args:
        stage: ambiente del token (`dev` | `local` | `stage`).
        private_key_b64: clave privada Ed25519 (base64 urlsafe).
        now: timestamp Unix de emision.
        ttl: ventana de validez en segundos (default 300).

    Returns:
        El token compacto `b64url(payload).b64url(sig)`.
    """
    payload = build_payload(stage=stage, now=now, ttl=ttl)
    payload_segment = _b64url_encode(
        json.dumps(payload, sort_keys=True, separators=(',', ':')).encode(
            'utf-8',
        ),
    )
    signature = _sign_message(private_key_b64, payload_segment.encode('ascii'))
    return f'{payload_segment}.{_b64url_encode(signature)}'
