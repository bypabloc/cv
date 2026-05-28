"""Builders compartidos para los tests unit del Lambda `auth_email_worker`.

Prefijo `_` para que pytest NO recolecte este archivo como tests.
"""

from __future__ import annotations

from typing import Any

# UUIDv7 valido determinista para los tests (version=7 en pos 14).
_DEFAULT_USER_ID = '019e5c50-0000-7000-8000-000000000001'
_DEFAULT_TO = 'user@example.com'
_DEFAULT_VERIFY_URL = (
    'https://api.portfolio.dev.the-full-stack.com/auth'
    '?operation=register&action=verify-magic-link&token=demo'
)
_DEFAULT_CODE = '7F3KQ29X'
_DEFAULT_EXPIRES_IN_MIN = 15


def magic_link_message(
    *,
    kind: str = 'register-magic-link',
    to: str = _DEFAULT_TO,
    user_id: str = _DEFAULT_USER_ID,
    niche: str | None = None,
    verify_url: str = _DEFAULT_VERIFY_URL,
    expires_in_min: int = _DEFAULT_EXPIRES_IN_MIN,
) -> dict[str, Any]:
    """Construye un body de magic-link valido."""
    return {
        'kind': kind,
        'to': to,
        'user_id': user_id,
        'niche': niche,
        'subject_id': f'auth.{kind}.subject',
        'data': {
            'verify_url': verify_url,
            'expires_in_min': expires_in_min,
        },
    }


def code_message(
    *,
    kind: str = 'register-code',
    to: str = _DEFAULT_TO,
    user_id: str = _DEFAULT_USER_ID,
    niche: str | None = None,
    code: str = _DEFAULT_CODE,
    expires_in_min: int = _DEFAULT_EXPIRES_IN_MIN,
) -> dict[str, Any]:
    """Construye un body de code valido."""
    return {
        'kind': kind,
        'to': to,
        'user_id': user_id,
        'niche': niche,
        'subject_id': f'auth.{kind}.subject',
        'data': {
            'code': code,
            'expires_in_min': expires_in_min,
        },
    }
