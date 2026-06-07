"""Recovery codes service: genera, persiste (hash) y consume.

Envuelve `shared.auth.recovery_codes` + el repository. `generate` SIEMPRE
regenera (borra los viejos del user + inserta 10 nuevos), asi cubre tanto
el primer generate (AC-7) como el regenerate (AC-8). Devuelve los codes
en plain text UNA vez; el backend solo guarda el hash SHA-256.
"""

from __future__ import annotations

from uuid import UUID

from shared.auth.recovery_codes import (
    generate_recovery_codes,
    hash_recovery_code,
)
from shared.db.repositories.auth_mfa import (
    consume_recovery_code,
    regenerate_recovery_codes,
)
from shared.db.repositories.auth_users import (
    count_recovery_codes,
    count_remaining_recovery_codes,
)
from shared.db.session import db_session


class RecoveryCodesService:
    """Generacion + consumo de recovery codes de MFA."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def generate(self, *, user_id: UUID | str) -> list[str]:
        """Borra los codes viejos del user, emite 10 nuevos (plain UNA vez)."""
        codes = generate_recovery_codes()
        hashes = [hash_recovery_code(code) for code in codes]
        with db_session() as session:
            regenerate_recovery_codes(
                session,
                user_id=str(user_id),
                code_hashes=hashes,
            )
        return codes

    def consume(self, *, user_id: UUID | str, code: str) -> bool:
        """Consume un code activo. False si no existe o ya fue consumido."""
        code_hash = hash_recovery_code(code)
        with db_session() as session:
            return consume_recovery_code(
                session,
                user_id=str(user_id),
                code_hash=code_hash,
            )

    def counts(self, *, user_id: UUID | str) -> dict[str, int]:
        """`{total, remaining}` de recovery codes del user (overview)."""
        with db_session() as session:
            return {
                'total': count_recovery_codes(session, user_id=str(user_id)),
                'remaining': count_remaining_recovery_codes(
                    session,
                    user_id=str(user_id),
                ),
            }
