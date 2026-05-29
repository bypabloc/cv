"""@module auth.consent_log — tabla `auth_user_consent_log` (GDPR consent)."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class AuthUserConsentLog(Base):
    """Log inmutable de cambios de consentimiento (GDPR).

    Cada cambio de `marketing_consent` (o `privacy_policy_version`) del
    user genera un row con el valor viejo y el nuevo, la IP y el
    user_agent. Sirve de evidencia de consentimiento ante una auditoria
    GDPR.

    `field` identifica que cambio (`'marketing_consent'` |
    `'privacy_policy'`). `old_value` / `new_value` son texto (el valor
    serializado, ej. `'true'` / `'false'`).
    """

    __tablename__ = 'auth_user_consent_log'

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text('uuidv7()'),
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('auth_users.id', ondelete='CASCADE'),
        nullable=False,
    )

    field: Mapped[str] = mapped_column(String(32), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    ip: Mapped[str | None] = mapped_column(INET(), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
