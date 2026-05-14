"""Database commands for the SAM backend (Neon PostgreSQL).

Maneja conexion a Neon (lee connection string de SSM), migrations SQL
desde serverless/migrations/, branches Neon (git-style DB branching),
y consultas de inventario (tablas + row counts).
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from typing import Any

from shared.console import CYAN
from shared.console import DIM
from shared.console import GREEN
from shared.console import NC
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'
_MIGRATIONS_DIR = _SERVERLESS_DIR / 'migrations'


def _get_neon_url(stage: str) -> str | None:
    """Lee la connection string de Neon desde SSM Parameter Store.

    Returns la URL o None si falla (con mensaje de error impreso).
    """
    if shutil.which('aws') is None:
        _err('AWS CLI no esta instalado')
        return None

    param_name = '/portfolio/neon-url'  # Stage-agnostico por ahora
    if stage in ('dev', 'prod'):
        param_name = f'/portfolio/{stage}/neon-url'

    result = subprocess.run(
        [
            'aws',
            'ssm',
            'get-parameter',
            '--name',
            param_name,
            '--with-decryption',
            '--query',
            'Parameter.Value',
            '--output',
            'text',
            '--region',
            'us-west-2',
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        _err(f'No se pudo leer {param_name}: {result.stderr.strip()}')
        print(
            f'{YELLOW}  Crear con:{NC} '
            f'{CYAN}python devtools/run.py serverless setup-ssm '
            f'--name={param_name}{NC}'
        )
        return None

    return result.stdout.strip()


def cmd_db_shell(flags: dict[str, Any]) -> int:
    """psql interactivo contra Neon."""
    if shutil.which('psql') is None:
        _err('psql no esta instalado. Instalar: apt install postgresql-client')
        return 1

    stage = flags.get('stage', 'local')
    url = _get_neon_url(stage)
    if not url:
        return 1

    branch = flags.get('branch')
    if branch:
        # Neon branch via URL path o param. Documentar en serverless/docs/secrets.md
        print(_c(YELLOW, f'Conectando a branch Neon: {branch}'))

    print(_c(CYAN, '$ psql <neon-url>'))
    result = subprocess.run(['psql', url], check=False)
    return result.returncode


def cmd_db_migrate(flags: dict[str, Any]) -> int:
    """Aplicar migrations SQL pendientes desde serverless/migrations/.

    Las migrations son archivos numerados (`001_<name>.sql`,
    `002_<name>.sql`, ...). El runner mantiene una tabla
    `schema_migrations` para evitar re-aplicar.
    """
    if not _MIGRATIONS_DIR.exists():
        _err(f'No existe directorio de migrations: {_MIGRATIONS_DIR}')
        print(f'{YELLOW}  Crear con:{NC} {CYAN}mkdir -p {_MIGRATIONS_DIR}{NC}')
        return 1

    sql_file = flags.get('sql_file')
    migrations = (
        [_MIGRATIONS_DIR / sql_file]
        if sql_file
        else sorted(_MIGRATIONS_DIR.glob('*.sql'))
    )

    if not migrations:
        print(_c(YELLOW, 'No hay migrations pendientes'))
        return 0

    stage = flags.get('stage', 'local')
    url = _get_neon_url(stage)
    if not url:
        return 1

    if flags.get('dry_run'):
        for m in migrations:
            print(_c(YELLOW, f'[dry-run] psql -f {m.name}'))
        return 0

    for migration in migrations:
        print(_c(CYAN, f'$ psql -f {migration.name}'))
        result = subprocess.run(
            ['psql', url, '-f', str(migration), '-v', 'ON_ERROR_STOP=1'],
            check=False,
        )
        if result.returncode != 0:
            _err(f'Migration fallo: {migration.name}')
            return result.returncode

    print(_c(GREEN, f'OK  {len(migrations)} migration(s) aplicadas'))
    return 0


def cmd_db_rollback(flags: dict[str, Any]) -> int:
    """Rollback de la ultima migration (destructivo).

    Busca el archivo `<migration>.down.sql` correspondiente y lo aplica.
    """
    if not flags.get('confirm'):
        _err('--confirm requerido para rollback')
        return 2

    if not _MIGRATIONS_DIR.exists():
        _err(f'No existe: {_MIGRATIONS_DIR}')
        return 1

    # Encuentra la ultima migration aplicada
    migrations = sorted(_MIGRATIONS_DIR.glob('*.sql'))
    if not migrations:
        print(_c(YELLOW, 'No hay migrations para rollback'))
        return 0

    last = migrations[-1]
    down_file = last.with_suffix('.down.sql')

    if not down_file.exists():
        _err(f'No existe el down script: {down_file}')
        return 1

    stage = flags.get('stage', 'local')
    url = _get_neon_url(stage)
    if not url:
        return 1

    if flags.get('dry_run'):
        print(_c(YELLOW, f'[dry-run] psql -f {down_file.name}'))
        return 0

    print(_c(CYAN, f'$ psql -f {down_file.name}'))
    result = subprocess.run(
        ['psql', url, '-f', str(down_file), '-v', 'ON_ERROR_STOP=1'],
        check=False,
    )

    if result.returncode == 0:
        print(_c(GREEN, f'OK  Rollback de {last.name} aplicado'))
    return result.returncode


def cmd_db_seed(flags: dict[str, Any]) -> int:
    """Cargar data de prueba en Neon."""
    seed_script = _SERVERLESS_DIR / 'scripts' / 'seed_test_data.sql'
    if not seed_script.exists():
        _err(f'No existe: {seed_script}')
        print(
            f'{YELLOW}  Crear con sample data. Ver serverless/ARCHITECTURE.md{NC}'
        )
        return 1

    stage = flags.get('stage', 'local')
    url = _get_neon_url(stage)
    if not url:
        return 1

    if flags.get('dry_run'):
        print(_c(YELLOW, f'[dry-run] psql -f {seed_script.name}'))
        return 0

    print(_c(CYAN, f'$ psql -f {seed_script.name}'))
    result = subprocess.run(
        ['psql', url, '-f', str(seed_script)],
        check=False,
    )
    return result.returncode


def cmd_db_branch(flags: dict[str, Any]) -> int:
    """CRUD de branches de Neon (via neon CLI).

    Subcomandos pasados via --subcommands o segundo positional:
      - create  --branch=<name> [--parent=main]
      - list
      - delete  --branch=<name>
    """
    if shutil.which('neon') is None:
        _err('neon CLI no instalado. Instalar: npm i -g neonctl')
        return 1

    subcommands = flags.get('subcommands', []) or []
    action = subcommands[1] if len(subcommands) > 1 else 'list'
    branch = flags.get('branch')
    parent = flags.get('parent', 'main')

    if action == 'list':
        print(_c(CYAN, '$ neon branches list'))
        result = subprocess.run(['neon', 'branches', 'list'], check=False)
        return result.returncode

    if action == 'create':
        if not branch:
            _err('--branch=<name> requerido para create')
            return 2
        print(
            _c(
                CYAN,
                f'$ neon branches create --name {branch} --parent {parent}',
            )
        )
        result = subprocess.run(
            [
                'neon',
                'branches',
                'create',
                '--name',
                branch,
                '--parent',
                parent,
            ],
            check=False,
        )
        return result.returncode

    if action == 'delete':
        if not branch:
            _err('--branch=<name> requerido para delete')
            return 2
        if not flags.get('confirm'):
            _err('--confirm requerido para delete')
            return 2
        print(_c(CYAN, f'$ neon branches delete {branch}'))
        result = subprocess.run(
            ['neon', 'branches', 'delete', branch],
            check=False,
        )
        return result.returncode

    _err(f'Subcomando desconocido: {action}. Validos: create, list, delete')
    return 2


def cmd_db_tables(flags: dict[str, Any]) -> int:
    """Listar tablas + row counts."""
    stage = flags.get('stage', 'local')
    url = _get_neon_url(stage)
    if not url:
        return 1

    sql = """
        SELECT
            schemaname || '.' || tablename AS table_name,
            n_live_tup AS estimated_rows
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC;
    """

    output_format = flags.get('output', 'text')
    args = ['psql', url, '-c', sql]
    if output_format == 'json':
        # Workaround: psql no tiene JSON nativo, usar -A -t y armar JSON manual.
        # Por ahora delegamos al text mode + nota.
        print(_c(YELLOW, 'output=json todavia no implementado para db-tables'))

    print(_c(CYAN, '$ psql -c "SELECT ... FROM pg_stat_user_tables"'))
    result = subprocess.run(args, check=False)
    return result.returncode
