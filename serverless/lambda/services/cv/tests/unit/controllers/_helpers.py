"""Helpers compartidos por los tests de controllers de las operations admin del `cv`.

Prefijo `_` para que pytest no recolecte el modulo. Builders puros que
arman eventos sinteticos + mocks de AuthUser + payloads validos por
entidad (shape YAML del seed).
"""

from __future__ import annotations

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
    """Evento autenticado (todas las actions llevan Authorization)."""
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


def _make_admin_user(
    *,
    user_id: UUID | str | None = None,
    email: str = 'admin@example.com',
) -> Any:
    """Mock de AuthUser admin (email en la whitelist del conftest)."""
    user = MagicMock()
    user.id = str(user_id) if user_id is not None else str(uuid4())
    user.email = email
    return user


def _experience_payload(slug: str = 'smoke-exp') -> dict[str, Any]:
    """Payload valido minimo de upsert-experience (shape YAML del seed)."""
    return {
        'slug': slug,
        'role': {'es': 'Dev de prueba', 'en': 'Smoke Dev'},
        'company': 'Smoke Corp',
        'country': 'Chile',
        'start': '2024-01',
        'seniority': 'senior',
        'niches': ['generic'],
        'priority': {'generic': 10},
    }


def _project_payload(slug: str = 'smoke-proj') -> dict[str, Any]:
    """Payload valido minimo de upsert-project (shape YAML del seed)."""
    return {
        'slug': slug,
        'name': 'Smoke Project',
        'summary': {'es': 'Resumen', 'en': 'Summary'},
        'status': 'active',
        'projectType': 'web',
        'stack': ['Python'],
        'niches': ['generic'],
    }
