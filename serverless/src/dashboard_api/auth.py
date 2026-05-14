"""Basic auth: bcrypt hash en SSM vs Authorization header del request."""

from __future__ import annotations

import base64
import os
from typing import Any

from common.exceptions import ApplicationError


class UnauthorizedError(ApplicationError):
    """HTTP 401 - basic auth invalido."""

    default_code = 'UNAUTHORIZED'
    status_code = 401


def parse_basic_auth(headers: dict[str, str]) -> tuple[str, str] | None:
    """
    Parsea Authorization: Basic <base64(user:pass)>.

    Returns:
        (user, password) o None si no presente.
    """
    auth = None
    for k, v in (headers or {}).items():
        if k.lower() == 'authorization':
            auth = v
            break
    if not auth or not auth.lower().startswith('basic '):
        return None
    try:
        encoded = auth.split(' ', 1)[1]
        decoded = base64.b64decode(encoded).decode('utf-8')
        if ':' not in decoded:
            return None
        user, password = decoded.split(':', 1)
        return user, password
    except (ValueError, UnicodeDecodeError):
        return None


def verify_basic_auth(headers: dict[str, str]) -> None:
    """
    Valida basic auth contra SSM-stored bcrypt hash.

    Raises:
        UnauthorizedError: si la auth es invalida o ausente.
    """
    parsed = parse_basic_auth(headers)
    if parsed is None:
        msg = 'Authorization header missing or malformed'
        raise UnauthorizedError(msg, code='AUTH_MISSING')

    _user, password = parsed

    # Comparar con SSM hash
    from common.ssm_client import get_secret  # noqa: PLC0415

    hash_path = os.environ.get(
        'SSM_DASHBOARD_HASH_PATH', '/portfolio/dashboard-password-hash'
    )
    try:
        stored_hash = get_secret(hash_path)
    except Exception as e:  # noqa: BLE001
        msg = f'Failed to fetch dashboard hash: {e}'
        raise UnauthorizedError(msg, code='AUTH_CONFIG_ERROR') from e

    # bcrypt verify (lazy import - solo se carga si auth se intenta)
    try:
        import bcrypt  # noqa: PLC0415
    except ImportError as e:
        msg = 'bcrypt not available'
        raise UnauthorizedError(msg, code='AUTH_LIB_MISSING') from e

    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
        msg = 'Invalid credentials'
        raise UnauthorizedError(msg, code='AUTH_INVALID')


def unauthorized_response(origin: str) -> dict[str, Any]:
    """Build 401 response con WWW-Authenticate header."""
    return {
        'statusCode': 401,
        'headers': {
            'Content-Type': 'application/json',
            'WWW-Authenticate': 'Basic realm="Portfolio Dashboard"',
            'Access-Control-Allow-Origin': origin,
            'Vary': 'Origin',
        },
        'body': '{"error":"Unauthorized","code":"UNAUTHORIZED"}',
    }
