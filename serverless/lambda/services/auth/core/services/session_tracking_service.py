"""Session tracking service del Lambda `auth` (plan 03).

Mantiene la tabla `auth_user_sessions` (sesiones activas por family_id de
refresh) que el Lambda `users` lee/revoca. Se llama tras CADA emision de
tokens terminales (creacion de sesion), en cada `session.refresh`
(rotation -> bump last_active_at) y en `session.logout` (delete).

DISENO: todas las escrituras son BEST-EFFORT. Un fallo de Neon (o que la
tabla aun no exista, pre-migration) NO debe romper el login/refresh/logout
— solo se loggea y se continua. El tracking es metadata, no parte del
camino critico de autenticacion.
"""

from __future__ import annotations

from uuid import UUID

from shared.db.repositories.auth_users import (
    delete_session_by_family,
    insert_user_session,
    rotate_session_family_id,
)
from shared.db.session import db_session
from shared.observability.logger import logger


def _parse_device_info(user_agent: str | None) -> dict[str, str]:
    """Deriva {browser, os, device_type} del user-agent (heuristica simple).

    Regex/substring liviano para no agregar deps. Devuelve dict vacio si el
    user_agent es None.
    """
    if not user_agent:
        return {}
    ua = user_agent.lower()

    browser = 'unknown'
    for needle, name in (
        ('edg/', 'edge'),
        ('opr/', 'opera'),
        ('chrome/', 'chrome'),
        ('firefox/', 'firefox'),
        ('safari/', 'safari'),
    ):
        if needle in ua:
            browser = name
            break

    os_name = 'unknown'
    for needle, name in (
        ('windows', 'windows'),
        ('mac os', 'macos'),
        ('android', 'android'),
        ('iphone', 'ios'),
        ('ipad', 'ios'),
        ('linux', 'linux'),
    ):
        if needle in ua:
            os_name = name
            break

    device_type = (
        'mobile'
        if any(token in ua for token in ('mobile', 'iphone', 'android'))
        else 'desktop'
    )
    return {'browser': browser, 'os': os_name, 'device_type': device_type}


class SessionTrackingService:
    """Track sesiones activas en `auth_user_sessions` (best-effort)."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def on_session_created(
        self,
        *,
        user_id: UUID | str,
        family_id: UUID | str,
        ip: str | None = None,
        country: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """INSERT una sesion nueva (login). Best-effort."""
        try:
            with db_session() as session:
                insert_user_session(
                    session,
                    user_id=str(user_id),
                    family_id=str(family_id),
                    device_info=_parse_device_info(user_agent),
                    ip=ip,
                    country=country,
                    user_agent=user_agent,
                )
        except Exception:
            logger.exception(
                'session_tracking on_session_created failed',
                extra={'user_id': str(user_id)},
            )

    def on_session_rotated(
        self,
        *,
        old_family_id: UUID | str,
        new_family_id: UUID | str,
    ) -> None:
        """Rota el family_id de la sesion (refresh) + bump last_active_at.

        En el refresh actual `old == new` (el family se mantiene), asi que
        es un bump de actividad. Best-effort.
        """
        try:
            with db_session() as session:
                rotate_session_family_id(
                    session,
                    old_family_id=str(old_family_id),
                    new_family_id=str(new_family_id),
                )
        except Exception:
            logger.exception('session_tracking on_session_rotated failed')

    def on_session_revoked(self, *, family_id: UUID | str) -> None:
        """DELETE la sesion de una family (logout). Best-effort."""
        try:
            with db_session() as session:
                delete_session_by_family(
                    session, family_id=str(family_id),
                )
        except Exception:
            logger.exception('session_tracking on_session_revoked failed')
