"""Helpers compartidos por los tests de controllers de `users`.

Prefijo `_` para que pytest no recolecte el modulo. Builders puros que
arman eventos sinteticos + mocks de AuthUser / JwtClaims / sesiones.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

_FAKE_BEARER = 'Bearer FAKE-ACCESS-JWT-FOR-TEST-XXXXXXXXXXXXXXXXXXXX'


def _make_authed_event(
    *,
    data: dict[str, Any] | None = None,
    authorization: str | None = _FAKE_BEARER,
    ip: str = '203.0.113.10',
    country: str = 'CL',
    user_agent: str = 'pytest',
) -> dict[str, Any]:
    """Evento autenticado (profile/status/admin con Authorization en _meta)."""
    event: dict[str, Any] = dict(data or {})
    event['_meta'] = {
        'ip': ip,
        'country': country,
        'user_agent': user_agent,
        'origin': 'https://admin.portfolio.dev.the-full-stack.com',
        'authorization': authorization,
        'cloudfront_meta': {},
    }
    return event


def _make_public_event(
    *,
    data: dict[str, Any] | None = None,
    ip: str = '203.0.113.10',
    country: str = 'CL',
    user_agent: str = 'pytest',
) -> dict[str, Any]:
    """Evento publico (confirm-email-change: sin Authorization)."""
    event: dict[str, Any] = dict(data or {})
    event['_meta'] = {
        'ip': ip,
        'country': country,
        'user_agent': user_agent,
        'origin': 'https://admin.portfolio.dev.the-full-stack.com',
        'cloudfront_meta': {},
    }
    return event


def _make_user(
    *,
    user_id: UUID | str | None = None,
    email: str = 'visitor@example.com',
    status: str = 'active',
    display_name: str | None = None,
    locale: str = 'en',
    timezone: str = 'UTC',
    marketing_consent: bool = False,
    failed_attempts: int = 0,
) -> Any:
    """Mock de AuthUser con los campos que usan los controllers de users."""
    from shared.db.models.auth import AuthUserStatus

    user = MagicMock()
    user.id = str(user_id) if user_id is not None else str(uuid4())
    user.email = email
    user.status = AuthUserStatus(status)
    user.display_name = display_name
    user.locale = locale
    user.timezone = timezone
    user.marketing_consent = marketing_consent
    user.failed_attempts = failed_attempts
    user.deleted_at = None
    user.locked_until = None
    user.email_verified_at = datetime(2026, 1, 1, tzinfo=UTC)
    user.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    return user


def _make_access_claims(
    *,
    user_id: UUID | str | None = None,
    family_id: UUID | str | None = None,
    jti: UUID | None = None,
    exp: int = 9999999999,
) -> Any:
    """Mock de JwtClaims access (incluye family_id de la sesion en curso)."""
    return SimpleNamespace(
        sub=user_id or uuid4(),
        jti=jti or uuid4(),
        typ='access',
        flow=None,
        step=None,
        exp=exp,
        family_id=family_id,
    )
