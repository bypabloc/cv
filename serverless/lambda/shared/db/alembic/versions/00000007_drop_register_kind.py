"""drop_register_kind

Revision ID: 00000007
Revises: 00000006
Create Date: 2026-06-05

Elimina el valor `register` de los tipos PostgreSQL `auth_code_kind` y
`auth_link_kind` (plan remove-register): el alta de usuarios se fusiono en el
flujo `login` unico (`login.start` crea el user pending), asi que la operation
`register` y su kind ya no se generan.

PostgreSQL NO soporta `ALTER TYPE ... DROP VALUE`, asi que se recrea el tipo:
  1. DELETE de las filas con `kind='register'` (deben ser 0 o filas inactivas:
     codes/links ya consumidos o expirados; el `ALTER COLUMN ... USING` falla
     si queda alguna). Verificado al planificar: dev 143 filas inactivas, prod 0.
  2. RENAME del tipo viejo a `<tipo>_old`.
  3. CREATE del tipo nuevo SIN `register`.
  4. ALTER de la columna que lo usa al tipo nuevo (cast via text).
  5. DROP del tipo viejo.

`auth_code_kind` lo usa `auth_email_codes.kind`; valores nuevos:
  ('login', 'password_reset').
`auth_link_kind` lo usa `auth_magic_links.kind`; valores nuevos:
  ('login', 'password_reset', 'email-change').

El `downgrade()` re-agrega `register` recreando los tipos con el valor (no se
restauran las filas borradas — eran efimeras). NO se corre en prod.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '00000007'
down_revision: str | None = '00000006'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _swap_enum(
    *,
    type_name: str,
    table: str,
    column: str,
    new_values: tuple[str, ...],
) -> None:
    """Recrea un tipo enum con `new_values` y re-apunta `table.column`.

    Borra primero las filas cuyo `column` no esta en `new_values` (no
    castearian). PostgreSQL no tiene DROP VALUE: rename-old + create-new +
    alter-column (USING cast via text) + drop-old.
    """
    values_csv = ', '.join(f"'{v}'" for v in new_values)
    keep_csv = ', '.join(f"'{v}'" for v in new_values)
    op.execute(
        f'DELETE FROM {table} WHERE {column}::text NOT IN ({keep_csv})',  # noqa: S608
    )
    op.execute(f'ALTER TYPE {type_name} RENAME TO {type_name}_old')
    op.execute(f'CREATE TYPE {type_name} AS ENUM ({values_csv})')
    op.execute(
        f'ALTER TABLE {table} ALTER COLUMN {column} '
        f'TYPE {type_name} USING {column}::text::{type_name}',
    )
    op.execute(f'DROP TYPE {type_name}_old')


def upgrade() -> None:
    _swap_enum(
        type_name='auth_code_kind',
        table='auth_email_codes',
        column='kind',
        new_values=('login', 'password_reset'),
    )
    _swap_enum(
        type_name='auth_link_kind',
        table='auth_magic_links',
        column='kind',
        new_values=('login', 'password_reset', 'email-change'),
    )


def downgrade() -> None:
    _swap_enum(
        type_name='auth_code_kind',
        table='auth_email_codes',
        column='kind',
        new_values=('register', 'login', 'password_reset'),
    )
    _swap_enum(
        type_name='auth_link_kind',
        table='auth_magic_links',
        column='kind',
        new_values=('register', 'login', 'password_reset', 'email-change'),
    )
