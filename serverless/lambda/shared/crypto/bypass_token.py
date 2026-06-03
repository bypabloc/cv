"""Contrato del token de bypass de Turnstile firmado con Ed25519.

Reemplaza el secreto fijo compartido (`X-Turnstile-Bypass-Secret`) por un
token EFIMERO firmado. El firmante (runner E2E / dev local) tiene la clave
PRIVADA; el Lambda verifica con la PUBLICA. Un leak del entorno del Lambda
(solo publica) NO permite forjar tokens.

Formato compacto (2 segmentos, sin padding):

    token = b64url(payload_json) "." b64url(signature)

- `payload_json`: JSON canonico de `{v, iat, exp, jti, stage}` con
  `sort_keys=True` y separadores compactos.
- `signature`: Ed25519 sobre los BYTES ASCII del primer segmento
  (`b64url(payload_json)`), NO sobre el JSON crudo — evita ambiguedad de
  serializacion entre firmante y verificador.

Stateless: la unica defensa anti-reuso es `exp` (TTL corto). No hay store
de nonce. `jti` existe solo para trazabilidad en logs (NUNCA se enforce
single-use).

`sign_bypass_token` vive aca (no solo en devtools) para que el FORMATO
tenga una unica fuente de verdad compartida por firmante y verificador.
El Lambda solo usa `verify_bypass_token`.
"""

from __future__ import annotations

import json
import secrets
from typing import Any

from shared.core.exceptions import BypassTokenError
from shared.crypto.ed25519 import (
    _b64url_decode,
    _b64url_encode,
    sign_message,
    verify_signature,
)

TOKEN_VERSION = 1
DEFAULT_TTL_SECONDS = 300


def build_payload(
    *,
    stage: str,
    now: int,
    ttl: int = DEFAULT_TTL_SECONDS,
) -> dict[str, Any]:
    """Construye el payload del token de bypass.

    Args:
        stage: ambiente al que se ata el token (`dev` | `local` | `stage`).
        now: timestamp Unix (segundos) de emision. Se pasa explicito para
            no llamar a `time.time()` aca (testeable + sin side-effects).
        ttl: ventana de validez en segundos (default 300).

    Returns:
        Dict `{v, iat, exp, jti, stage}`.
    """
    return {
        'v': TOKEN_VERSION,
        'iat': now,
        'exp': now + ttl,
        'jti': secrets.token_hex(8),
        'stage': stage,
    }


def _encode_payload(payload: dict[str, Any]) -> str:
    """Serializa el payload a JSON canonico y lo codifica en b64url."""
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return _b64url_encode(raw)


def sign_bypass_token(
    *,
    stage: str,
    private_key_b64: str,
    now: int,
    ttl: int = DEFAULT_TTL_SECONDS,
) -> str:
    """Emite un token de bypass firmado (lo usa tests/shared via el comando e2e).

    Args:
        stage: ambiente del token.
        private_key_b64: clave privada Ed25519 (base64 urlsafe).
        now: timestamp Unix de emision.
        ttl: ventana de validez en segundos.

    Returns:
        El token compacto `b64url(payload).b64url(sig)`.
    """
    payload = build_payload(stage=stage, now=now, ttl=ttl)
    payload_segment = _encode_payload(payload)
    signature = sign_message(private_key_b64, payload_segment.encode('ascii'))
    return f'{payload_segment}.{_b64url_encode(signature)}'


def verify_bypass_token(
    token: str,
    *,
    public_key_b64: str,
    stage: str,
    now: int,
) -> dict[str, Any]:
    """Verifica un token de bypass firmado.

    Validaciones (en orden): formato -> firma -> version -> expiracion ->
    stage. CUALQUIER fallo levanta `BypassTokenError` SIN incluir el token
    en el mensaje (defensa: no filtrar el token en logs).

    Args:
        token: el token recibido en el header `X-Turnstile-Bypass-Token`.
        public_key_b64: clave publica Ed25519 del stage (base64 urlsafe).
        stage: `STAGE` del Lambda — debe coincidir con `payload.stage`.
        now: timestamp Unix actual (se pasa explicito; testeable).

    Returns:
        El payload validado.

    Raises:
        BypassTokenError: con `code` especifico (MALFORMED / BAD_SIGNATURE /
            BAD_VERSION / EXPIRED / STAGE_MISMATCH).
    """
    segments = token.split('.') if token else []
    if len(segments) != 2 or not segments[0] or not segments[1]:
        raise BypassTokenError(
            'malformed bypass token',
            code='MALFORMED',
        )
    payload_segment, signature_segment = segments

    try:
        signature = _b64url_decode(signature_segment)
    except (ValueError, TypeError) as exc:
        raise BypassTokenError(
            'malformed bypass token signature',
            code='MALFORMED',
        ) from exc

    if not verify_signature(
        public_key_b64,
        payload_segment.encode('ascii'),
        signature,
    ):
        raise BypassTokenError(
            'bypass token signature mismatch',
            code='BAD_SIGNATURE',
        )

    # La firma valida garantiza que el payload no fue alterado; recien aca
    # se decodifica y parsea.
    try:
        payload_raw = _b64url_decode(payload_segment)
        payload = json.loads(payload_raw)
    except (ValueError, TypeError) as exc:
        raise BypassTokenError(
            'malformed bypass token payload',
            code='MALFORMED',
        ) from exc

    if not isinstance(payload, dict):
        raise BypassTokenError(
            'malformed bypass token payload',
            code='MALFORMED',
        )

    if payload.get('v') != TOKEN_VERSION:
        raise BypassTokenError(
            'unsupported bypass token version',
            code='BAD_VERSION',
        )

    exp = payload.get('exp')
    if not isinstance(exp, int) or now >= exp:
        raise BypassTokenError(
            'bypass token expired',
            code='EXPIRED',
        )

    if payload.get('stage') != stage:
        raise BypassTokenError(
            'bypass token stage mismatch',
            code='STAGE_MISMATCH',
        )

    return payload
