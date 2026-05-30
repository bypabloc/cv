"""Firma de tokens de bypass de Turnstile (Ed25519) — lado devtools.

ESPEJO de `serverless/lambda/shared/crypto/bypass_token.py` (el verificador
del Lambda). Mismo formato de token EXACTO para que un token firmado aca
sea verificable por el backend:

    token = b64url(payload_json) "." b64url(signature)

- `payload_json`: JSON canonico de `{v, iat, exp, jti, stage}` con
  `sort_keys=True` y separadores compactos.
- `signature`: Ed25519 sobre los BYTES ASCII del primer segmento.

devtools NO puede importar `shared.crypto` (colision de namespace con el
paquete `devtools/shared/`), por eso este modulo replica el formato. Hay
un test (`devtools/tests/test_bypass_token_matches_backend.py`) que ancla
la paridad firma-devtools / verifica-backend para que no se desincronicen.

Este modulo SOLO firma y genera claves (operaciones del firmante). El
Lambda solo verifica. La clave privada NUNCA debe loguearse ni salir del
entorno local (`docker/env/dev-cli/`).
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


def generate_keypair() -> tuple[str, str]:
    """Genera un par Ed25519 nuevo.

    Returns:
        `(private_key_b64, public_key_b64)` — 32 bytes raw cada una en
        base64 urlsafe sin padding. La privada NUNCA debe loguearse.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

    private_key = Ed25519PrivateKey.generate()
    private_raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return _b64url_encode(private_raw), _b64url_encode(public_raw)


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
