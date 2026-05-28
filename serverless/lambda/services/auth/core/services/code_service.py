"""Code service del Lambda `auth`.

Genera codes de 8 chars (Crockford-like alphabet, sin O/0/I/1/L) para
verificacion via email. Persiste el hash (SHA-256) en
`auth_email_codes` con TTL 15 min y consume el code con un compare
constant-time.

El code en claro se publica al worker (que lo embebe en el email del
visitante). El backend solo persiste el hash.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from shared.auth import compare_code, generate_code, hash_code
from shared.db import db_session
from shared.db.models import AuthCodeKind, AuthUser
from shared.db.repositories.auth import (
    consume_email_code,
    insert_email_code,
)

# TTL del code (politica MVP). El worker debe enviarlo antes del expiry.
_CODE_TTL = timedelta(minutes=15)


class CodeService:
    """Service de auth_email_codes (generate + verify)."""

    def __init__(self, app_config: object) -> None:
        """`app_config` se acepta por uniformidad (no se usa hoy)."""
        self.app_config = app_config

    def generate_and_persist(
        self,
        *,
        user_id: UUID | str,
        kind: AuthCodeKind,
    ) -> tuple[str, bytes]:
        """Genera un code de 8 chars + hash + lo persiste.

        Returns: tupla (code_plain, code_hash). El code_plain solo viaja
        al worker via SQS; el hash queda en Neon.
        """
        code = generate_code()
        code_hash = hash_code(code)
        expires_at = datetime.now(tz=UTC) + _CODE_TTL
        with db_session() as session:
            insert_email_code(
                session,
                user_id=str(user_id),
                code_hash=code_hash,
                kind=kind,
                expires_at=expires_at,
            )
        return code, code_hash

    def verify(
        self,
        *,
        user: AuthUser,
        kind: AuthCodeKind,
        code: str,
    ) -> bool:
        """Verifica el code en claro contra el hash persistido.

        El compare es constant-time (SHA-256(code) == row.code_hash).
        Side-effects en Neon:
          - Si OK: marca `consumed_at=now`.
          - Si WRONG (existe row valida pero code distinto): incrementa
            `attempts` en el row.

        Retorna True solo si el code matchea Y no esta expirado Y no
        fue consumido previamente.
        """
        candidate_hash = hash_code(code)
        with db_session() as session:
            session.add(user)
            consumed = consume_email_code(
                session,
                user_id=str(user.id),
                kind=kind,
                code_hash=candidate_hash,
            )
        # Defensa adicional: compare_code es constant-time. Si llegamos
        # con `consumed is None` (wrong/expired/consumed), retornamos
        # False sin filtrar el motivo (lo distingue el controller con
        # un select adicional si lo necesita).
        if consumed is None:
            # Constant-time compare con un hash dummy para evitar timing
            # side channels (decision MVP).
            _ = compare_code(code=code, stored_hash=candidate_hash)
            return False
        return True
