"""Helper privado del login con password (plan 02).

Lee el `password_hash` del row `auth_credentials` del user y lo verifica
con argon2id. Vive en la capa de controllers (NO es un service nuevo):
los services del plan 02 no exponen lectura del hash y la rule del plan
prohibe tocarlos, asi que el acceso de solo-lectura va aqui via
`shared.db`. NUNCA loggea el hash ni la password.

`check_password` devuelve True/False; NeedsRehashError de argon2 se
trata como match exitoso (el rehash es una optimizacion, no afecta el
login). Un user sin row de credentials (passwordless) devuelve False.
"""

from __future__ import annotations

from uuid import UUID

from shared.auth.password import NeedsRehashError, verify_password
from shared.db.models.auth.credentials import AuthCredentials
from shared.db.session import db_session


def get_password_hash(*, user_id: UUID | str) -> str | None:
    """Devuelve el password_hash del user, o None si no tiene credentials."""
    with db_session() as session:
        cred = session.get(AuthCredentials, str(user_id))
        return cred.password_hash if cred is not None else None


def check_password(*, user_id: UUID | str, password: str) -> bool:
    """True si la password matchea el hash del user.

    False si el user no tiene password seteada o no matchea. Trata
    NeedsRehashError de argon2 como match exitoso.
    """
    hashed = get_password_hash(user_id=user_id)
    if hashed is None:
        return False
    try:
        return verify_password(password=password, hashed=hashed)
    except NeedsRehashError:
        return True
