"""
Aplica migrations SQL contra Neon PostgreSQL.

Lee DB_URL desde env (cargado por devtools desde
docker/env/server/.{stage} — categoria server).
Itera migrations/*.sql en orden y aplica las que no esten en schema_migrations.

Uso:
    cd serverless
    DB_URL=<...> python scripts/migrate.py [up|down] [--target=<version>]

Default: `up` aplica todas las pending.
"""

from __future__ import annotations

import hashlib
import os
import sys
import time
from pathlib import Path


def _connect():
    """Lazy import psycopg para que el script funcione sin venv si solo lista."""
    import psycopg  # noqa: PLC0415

    db_url = os.environ.get('DB_URL')
    if not db_url:
        msg = 'DB_URL no esta seteada (esperado en docker/env/server/.{stage})'
        raise SystemExit(msg)
    return psycopg.connect(db_url)


def _list_migrations(direction: str = 'up') -> list[tuple[str, Path]]:
    """Retorna lista ordenada de (version, path) de migrations."""
    migrations_dir = Path(__file__).parent.parent / 'migrations'
    suffix = '.down.sql' if direction == 'down' else '.sql'
    skip_suffix = '.sql' if direction == 'down' else '.down.sql'
    files = []
    for path in sorted(migrations_dir.iterdir()):
        name = path.name
        if not name.endswith(suffix):
            continue
        if direction == 'up' and name.endswith('.down.sql'):
            continue
        if direction == 'down' and not name.endswith('.down.sql'):
            continue
        version = name.replace(suffix, '').replace('.down', '')
        files.append((version, path))
    if direction == 'down':
        files.reverse()
    return files


def _applied_versions(conn) -> set[str]:
    """Retorna versiones ya aplicadas (lee schema_migrations)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations')"
        )
        exists = cur.fetchone()[0]
        if not exists:
            return set()
        cur.execute('SELECT version FROM schema_migrations')
        return {row[0] for row in cur.fetchall()}


def _apply_migration(conn, version: str, path: Path) -> None:
    """Aplica una migration (lee SQL + ejecuta + log en schema_migrations)."""
    sql = path.read_text(encoding='utf-8')
    checksum = hashlib.sha256(sql.encode()).hexdigest()[:16]

    print(f'[migrate] applying {version}...')
    start = time.time()

    with conn.cursor() as cur:
        cur.execute(sql)
        # Si la migration creo schema_migrations, registramos
        # (si no existe la tabla aun, esta migration la creara - 005 case)
        cur.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations')"
        )
        if cur.fetchone()[0]:
            cur.execute(
                'INSERT INTO schema_migrations (version, checksum, duration_ms) '
                'VALUES (%s, %s, %s) ON CONFLICT (version) DO NOTHING',
                (version, checksum, int((time.time() - start) * 1000)),
            )

    duration_ms = int((time.time() - start) * 1000)
    print(f'[migrate]   {version} applied in {duration_ms}ms')


def up() -> int:
    """Aplica migrations pendientes."""
    with _connect() as conn:
        conn.autocommit = False
        applied = _applied_versions(conn)
        pending = [
            (v, p) for v, p in _list_migrations('up') if v not in applied
        ]
        if not pending:
            print('[migrate] no pending migrations')
            return 0
        print(f'[migrate] {len(pending)} pending migration(s)')
        for version, path in pending:
            try:
                _apply_migration(conn, version, path)
                conn.commit()
            except Exception:
                conn.rollback()
                print(f'[migrate]   FAILED {version} (rolled back)')
                raise
    print('[migrate] all migrations applied')
    return 0


def down(target: str | None = None) -> int:
    """Rollback hasta version (o todas si target=None)."""
    with _connect() as conn:
        conn.autocommit = False
        applied = _applied_versions(conn)
        files = [(v, p) for v, p in _list_migrations('down') if v in applied]
        if target:
            files = [(v, p) for v, p in files if v >= target]
        if not files:
            print('[migrate] nothing to rollback')
            return 0
        print(f'[migrate] rolling back {len(files)} migration(s)')
        for version, path in files:
            print(f'[migrate] reverting {version}')
            with conn.cursor() as cur:
                cur.execute(path.read_text(encoding='utf-8'))
                cur.execute(
                    'DELETE FROM schema_migrations WHERE version = %s',
                    (version,),
                )
            conn.commit()
    return 0


def status() -> int:
    """Lista migrations + status (applied/pending)."""
    with _connect() as conn:
        applied = _applied_versions(conn)
    for version, _ in _list_migrations('up'):
        mark = '✓ applied' if version in applied else '· pending'
        print(f'  {mark}  {version}')
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else 'up'
    if cmd == 'up':
        return up()
    if cmd == 'down':
        target = None
        for arg in argv[1:]:
            if arg.startswith('--target='):
                target = arg.split('=', 1)[1]
        return down(target)
    if cmd == 'status':
        return status()
    print(f'Usage: migrate.py [up|down|status]')
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
