"""@module auth.user — tabla `auth_users` (cuentas del sistema auth)."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base
from .enums import AuthUserStatus


class AuthUser(Base):
    """Usuario del sistema auth.

    `id` se autogenera con `uuidv7()` server-side (PG18). NO usa
    UUIDPKMixin porque agrega `created_at`/`updated_at` con onupdate y
    aqui los queremos explicitos junto a `last_login_at` y similares.

    `email` es CITEXT UNIQUE: el lookup es case-insensitive. El service
    lo guarda lowercased (`email.lower().strip()`) para que el index
    funcione optimo.

    `profile_id` FK NULLABLE a `cv_profiles.id` con ON DELETE SET NULL.
    Solo el row de Pablo apuntara (manual). El resto de users (visitantes
    autenticados, futuro plan 3) tiene `profile_id=NULL`.

    `status` enum PG `auth_user_status`. Default `pending`.
    `failed_attempts` se incrementa en cada verify wrong (code/password).
    Tras 5 fallos en 5 min: status -> `locked`, locked_until = now + 1h.
    """

    __tablename__ = 'auth_users'

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text('uuidv7()'),
    )

    email: Mapped[str] = mapped_column(
        CITEXT(), nullable=False, unique=True,
    )

    # ENUM nativo PG. El `name` DEBE coincidir con el `name` del tipo
    # creado en la migration ('auth_user_status'). `create_type=False`
    # evita que el autogenerate intente recrear el tipo en cada revision.
    # `values_callable` fuerza que SQLAlchemy serialize el value del
    # StrEnum (`'pending'`, `'active'`, ...) en lugar de el name.
    status: Mapped[AuthUserStatus] = mapped_column(
        SAEnum(
            AuthUserStatus,
            name='auth_user_status',
            create_type=False,
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
        server_default=text("'pending'::auth_user_status"),
    )

    profile_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('cv_profiles.id', ondelete='SET NULL'),
        nullable=True,
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    password_set_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    failed_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text('0'),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
