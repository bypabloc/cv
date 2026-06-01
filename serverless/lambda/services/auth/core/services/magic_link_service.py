"""Magic-link service del Lambda `auth`.

Genera tokens opacos b64url de 32 bytes y los persiste en
`auth_magic_links` (SHA-256 del token en `token_hash`, UNIQUE). El
plain NUNCA se persiste — solo viaja en la URL del email.

`verify(token)` busca el hash en Neon, valida que no este expirado ni
consumido, y lo marca consumed (single-use).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from shared.auth.tokens import generate_opaque_token, hash_token
from shared.db.models.auth.enums import AuthLinkKind
from shared.db.models.auth.magic_link import AuthMagicLink
from shared.db.repositories.auth import (
    consume_magic_link,
    get_magic_link_state,
    insert_magic_link,
)
from shared.db.session import db_session

# TTL del magic-link (politica MVP).
# LINK_TTL_MINUTES es la fuente unica: el email que envia el worker muestra
# este mismo valor (lo pasa el caller a EmailDispatchService.publish_magic_link).
LINK_TTL_MINUTES = 15
_LINK_TTL = timedelta(minutes=LINK_TTL_MINUTES)


class MagicLinkService:
    """Service de auth_magic_links (generate + verify)."""

    def __init__(self, app_config: object) -> None:
        """`app_config` se acepta por uniformidad (no se usa hoy)."""
        self.app_config = app_config

    def generate_and_persist(
        self,
        *,
        user_id: UUID | str,
        kind: AuthLinkKind,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[str, bytes]:
        """Genera un opaque token + hash + lo persiste.

        Returns: tupla (token_plain, token_hash). El plain viaja al
        worker en el payload SQS; el hash queda en Neon.
        """
        plain = generate_opaque_token()
        h = hash_token(plain)
        expires_at = datetime.now(tz=UTC) + _LINK_TTL
        with db_session() as session:
            insert_magic_link(
                session,
                user_id=str(user_id),
                token_hash=h,
                kind=kind,
                expires_at=expires_at,
                ip=ip,
                user_agent=user_agent,
            )
        return plain, h

    def verify(self, *, plain: str) -> AuthMagicLink | None:
        """Verifica el plain contra el hash persistido.

        Retorna el row si matchea (no expirado, no consumido); marca
        `consumed_at=now`. Retorna None si no matchea.
        """
        h = hash_token(plain)
        with db_session() as session:
            return consume_magic_link(session, token_hash=h)

    def get_state(self, *, plain: str) -> AuthMagicLink | None:
        """Devuelve el row SIN consumirlo, para distinguir errores.

        Lo usan los controllers `verify_magic_link` cuando `verify`
        retorna `None`, para diferenciar `LINK_CONSUMED` (consumed_at
        is not None) vs `LINK_EXPIRED` (expires_at <= now) vs no
        existe (None).
        """
        h = hash_token(plain)
        with db_session() as session:
            return get_magic_link_state(session, token_hash=h)
