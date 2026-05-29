"""Helpers compartidos por los tests de controllers de auth.

Prefijo `_` para que pytest no recolecte el modulo. Cada helper es una
funcion pura que arma un fixture minimo para un test (mock de service
con valor o evento sintetico).
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4


def _make_event_register_start(
    *,
    email: str = 'visitor@example.com',
    cf_token: str = 'TURNSTILE-OK',
    niche: str | None = None,
    ip: str = '203.0.113.10',
    country: str = 'CL',
    user_agent: str = 'pytest',
    bypass_secret: str | None = None,
) -> dict[str, Any]:
    """Arma el `controller_event` (data) tipico de register/start."""
    return {
        'email': email,
        'cf_turnstile_response': cf_token,
        'niche': niche,
        '_meta': {
            'ip': ip,
            'country': country,
            'user_agent': user_agent,
            'bypass_secret': bypass_secret,
            'origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'cloudfront_meta': {},
        },
    }


def _make_event_with_token(
    *,
    token: str = 'A' * 32,
    ip: str = '203.0.113.10',
    country: str = 'CL',
    user_agent: str = 'pytest',
) -> dict[str, Any]:
    """Evento de verify-magic-link (register o login)."""
    return {
        'token': token,
        '_meta': {
            'ip': ip,
            'country': country,
            'user_agent': user_agent,
            'bypass_secret': None,
            'origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'cloudfront_meta': {},
        },
    }


def _make_event_with_code(
    *,
    code: str = 'ABCDEFGH',
    temp_token: str = 'FAKE-TEMP-TOKEN-FOR-TEST-XXXXXXXXXXX',
    ip: str = '203.0.113.10',
    country: str = 'CL',
    user_agent: str = 'pytest',
) -> dict[str, Any]:
    """Evento de verify-code (register o login)."""
    return {
        'code': code,
        'temp_token': temp_token,
        '_meta': {
            'ip': ip,
            'country': country,
            'user_agent': user_agent,
            'bypass_secret': None,
            'origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'cloudfront_meta': {},
        },
    }


def _make_event_set_password(
    *,
    password: str = 'a-very-strong-passphrase-1',
    temp_token: str = 'FAKE-TEMP-TOKEN-FOR-TEST-XXXXXXXXXXX',
    ip: str = '203.0.113.10',
    country: str = 'CL',
    user_agent: str = 'pytest',
) -> dict[str, Any]:
    """Evento de verify/set-password."""
    return {
        'password': password,
        'temp_token': temp_token,
        '_meta': {
            'ip': ip,
            'country': country,
            'user_agent': user_agent,
            'bypass_secret': None,
            'origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'cloudfront_meta': {},
        },
    }


def _make_event_resend_code(
    *,
    temp_token: str = 'FAKE-TEMP-TOKEN-FOR-TEST-XXXXXXXXXXX',
    ip: str = '203.0.113.10',
    country: str = 'CL',
    user_agent: str = 'pytest',
) -> dict[str, Any]:
    """Evento de verify/resend-code."""
    return {
        'temp_token': temp_token,
        '_meta': {
            'ip': ip,
            'country': country,
            'user_agent': user_agent,
            'bypass_secret': None,
            'origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'cloudfront_meta': {},
        },
    }


def _make_event_refresh(
    *,
    refresh_token: str = 'FAKE-REFRESH-TOKEN-FOR-TEST-XXXXXXXX',
    ip: str = '203.0.113.10',
    country: str = 'CL',
    user_agent: str = 'pytest',
) -> dict[str, Any]:
    """Evento de session/refresh."""
    return {
        'refresh_token': refresh_token,
        '_meta': {
            'ip': ip,
            'country': country,
            'user_agent': user_agent,
            'bypass_secret': None,
            'origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'cloudfront_meta': {},
        },
    }


def _make_event_logout(
    *,
    access_token: str = 'FAKE-ACCESS-TOKEN-FOR-TEST-XXXXXXXXX',
    refresh_token: str | None = None,
    ip: str = '203.0.113.10',
    country: str = 'CL',
    user_agent: str = 'pytest',
) -> dict[str, Any]:
    """Evento de session/logout."""
    event: dict[str, Any] = {
        'access_token': access_token,
        '_meta': {
            'ip': ip,
            'country': country,
            'user_agent': user_agent,
            'bypass_secret': None,
            'origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'cloudfront_meta': {},
        },
    }
    if refresh_token is not None:
        event['refresh_token'] = refresh_token
    return event


_FAKE_BEARER = 'Bearer FAKE-ACCESS-JWT-FOR-TEST-XXXXXXXXXXXXXXXXXXXX'


def _make_authed_event(
    *,
    data: dict[str, Any] | None = None,
    authorization: str | None = _FAKE_BEARER,
    ip: str = '203.0.113.10',
    country: str = 'CL',
    user_agent: str = 'pytest',
) -> dict[str, Any]:
    """Evento autenticado (mfa.* / webauthn.* con Authorization en _meta)."""
    event: dict[str, Any] = dict(data or {})
    event['_meta'] = {
        'ip': ip,
        'country': country,
        'user_agent': user_agent,
        'bypass_secret': None,
        'origin': 'https://admin.portfolio.dev.the-full-stack.com',
        'authorization': authorization,
        'cloudfront_meta': {},
    }
    return event


def _make_temp_event(
    *,
    data: dict[str, Any] | None = None,
    ip: str = '203.0.113.10',
    country: str = 'CL',
    user_agent: str = 'pytest',
) -> dict[str, Any]:
    """Evento de un step con temp_token (sin Authorization)."""
    event: dict[str, Any] = dict(data or {})
    event['_meta'] = {
        'ip': ip,
        'country': country,
        'user_agent': user_agent,
        'bypass_secret': None,
        'origin': 'https://admin.portfolio.dev.the-full-stack.com',
        'cloudfront_meta': {},
    }
    return event


def _make_session_claims(
    *,
    user_id: UUID | None = None,
    typ: str = 'refresh',
    jti: UUID | None = None,
    family_id: UUID | None = None,
    exp: int = 9999999999,
) -> Any:
    """Mock de JwtClaims para access/refresh (session)."""
    return SimpleNamespace(
        sub=user_id or uuid4(),
        jti=jti or uuid4(),
        flow=None,
        step=None,
        exp=exp,
        typ=typ,
        family_id=family_id if family_id is not None else uuid4(),
    )


def _make_user(
    *,
    user_id: UUID | None = None,
    email: str = 'visitor@example.com',
    status: str = 'pending',
    failed_attempts: int = 0,
) -> Any:
    """Mock de AuthUser con los campos minimos que usan los controllers."""
    from shared.db.models import AuthUserStatus

    user = MagicMock()
    user.id = user_id or uuid4()
    user.email = email
    # Map del string al enum para que el controller use .value y matchee.
    user.status = AuthUserStatus(status)
    user.failed_attempts = failed_attempts
    return user


def _make_jwt_claims(
    *,
    user_id: UUID | None = None,
    flow: str = 'register',
    step: int = 1,
    jti: UUID | None = None,
    exp: int = 9999999999,
) -> Any:
    """Mock de JwtClaims minimo."""
    return SimpleNamespace(
        sub=user_id or uuid4(),
        jti=jti or uuid4(),
        flow=flow,
        step=step,
        exp=exp,
        typ='temp',
        family_id=None,
    )


def _make_magic_link(
    *,
    user_id: UUID | None = None,
    consumed: bool = False,
    expired: bool = False,
) -> Any:
    """Mock de AuthMagicLink."""
    link = MagicMock()
    link.user_id = user_id or uuid4()
    link.consumed_at = datetime.now(tz=UTC) if consumed else None
    link.expires_at = (
        datetime(2020, 1, 1, tzinfo=UTC)
        if expired
        else datetime(2099, 1, 1, tzinfo=UTC)
    )
    return link


def _patch_services(monkeypatch: Any, controller_module: Any) -> dict[str, Any]:
    """Patchea los services importados por el modulo del controller.

    Devuelve un dict {nombre_service: mock} para que el test seleccione
    el comportamiento (return_value, side_effect, ...).
    """
    mocks = {
        'UserService': MagicMock(),
        'CodeService': MagicMock(),
        'MagicLinkService': MagicMock(),
        'JwtService': MagicMock(),
        'EmailDispatchService': MagicMock(),
        'AuditService': MagicMock(),
        'RateLimitService': MagicMock(),
        'FlowService': MagicMock(),
    }
    for name, m in mocks.items():
        if hasattr(controller_module, name):
            instance = MagicMock()
            m.return_value = instance
            monkeypatch.setattr(controller_module, name, m)
            mocks[name] = instance  # the instance is what tests use
    return mocks
