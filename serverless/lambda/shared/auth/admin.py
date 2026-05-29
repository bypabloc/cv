"""@module shared.auth.admin — whitelist de admins via SSM.

El scope `admin.*` del Lambda `users` esta restringido a una lista de
emails leida de SSM `/portfolio/${stage}/admin-emails` (SecureString +
KMS). Rotar admins = editar el SSM (sin tocar codigo ni DB — decision 2
del plan 03).

La lista se cachea module-level con TTL para evitar un hit a SSM por
request. `require_admin` levanta `AdminAuthzError` con codigo `NOT_FOUND`
(status 404) y NO `FORBIDDEN`: ocultar la existencia del endpoint a un
caller no-admin es anti-enumeration (AC-11).

Convencion de imports: SOLO `shared.aws.get_secret_by_name` (boto3 viaja
por shared.aws); NO se agregan paquetes externos en este modulo.
"""

from __future__ import annotations

import time

from shared.aws.ssm import get_secret_by_name
from shared.core.exceptions import ApplicationError


class AdminAuthzError(ApplicationError):
    """El caller no es admin. Se reporta como 404 (anti-enumeration)."""

    default_code = 'NOT_FOUND'
    status_code = 404


# Cache module-level de la whitelist. Los tests deben resetearlo entre
# casos (fixture autouse) — ver `shared/tests/unit/shared/auth/conftest.py`.
_CACHE: dict[str, object] = {'emails': frozenset(), 'expires_at': 0.0}


def load_admin_emails(*, ttl: int = 300) -> frozenset[str]:
    """Carga la whitelist de admin emails desde SSM (cache TTL).

    Devuelve un frozenset de emails normalizados (lower + strip). Lista
    vacia si el SSM no tiene valor (== sin admins).
    """
    now = time.time()
    cached: frozenset[str] = _CACHE['emails']  # type: ignore[assignment]
    expires_at: float = _CACHE['expires_at']  # type: ignore[assignment]
    if expires_at > now and cached:
        return cached

    raw = get_secret_by_name('admin-emails', local_env='ADMIN_EMAILS')
    if not raw:
        emails: frozenset[str] = frozenset()
    else:
        emails = frozenset(
            piece.strip().lower()
            for piece in raw.split(',')
            if piece.strip()
        )

    _CACHE['emails'] = emails
    _CACHE['expires_at'] = now + ttl
    return emails


def is_admin(email: str, *, ttl: int = 300) -> bool:
    """True si `email` esta en la whitelist SSM (case-insensitive)."""
    return email.strip().lower() in load_admin_emails(ttl=ttl)


def require_admin(email: str) -> None:
    """Levanta `AdminAuthzError` (404) si `email` no es admin."""
    if not is_admin(email):
        raise AdminAuthzError('NOT_FOUND')
