"""Database commands for the SAM backend (Neon PostgreSQL).

El schema de Neon lo gestiona Alembic — los modelos SQLAlchemy de
`serverless/src/common/db/` son la unica fuente de verdad. Las migraciones
NO se aplican con `psql` desde aqui: se delegan a la Lambda `db`
(`portfolio-db-<stage>`), que corre Alembic dentro de AWS con la
connection string que el template inyecta desde SSM.

Este modulo:
- `db-migrate` / `db-rollback` / `db-current` / `db-show-migrations`:
  invocan la Lambda `db` via `aws lambda invoke`.
- `db-shell` / `db-tables` / `db-seed`: psql directo (no son migraciones).
- `db-branch`: CRUD de branches Neon (git-style) via el `neon` CLI.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

from shared.console import CYAN
from shared.console import DIM
from shared.console import GREEN
from shared.console import NC
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'


def _get_neon_url(stage: str) -> str | None:
    """Lee la connection string de Neon desde SSM Parameter Store.

    Solo la usan los comandos psql directos (`db-shell`, `db-tables`,
    `db-seed`). Las migraciones NO la usan — la Lambda `db` resuelve la URL
    por su cuenta dentro de AWS. Returns la URL o None si falla.
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
            'us-east-1',
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


def _invoke_db_lambda(
    stage: str, command: str, args: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """Invoca la Lambda `db` (`portfolio-db-<stage>`) con un comando Alembic.

    Construye el payload `{"command": ..., "args": {...}}`, lo invoca con
    `aws lambda invoke` y parsea la respuesta JSON. Returns el dict de
    respuesta, o None si la invocacion falla (con error impreso).
    """
    if shutil.which('aws') is None:
        _err('AWS CLI no esta instalado')
        return None

    function_name = f'portfolio-db-{stage}'
    payload: dict[str, Any] = {'command': command}
    if args:
        payload['args'] = args

    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / 'db-lambda-response.json'
        result = subprocess.run(
            [
                'aws',
                'lambda',
                'invoke',
                '--function-name',
                function_name,
                '--payload',
                json.dumps(payload),
                '--cli-binary-format',
                'raw-in-base64-out',
                '--region',
                'us-east-1',
                str(out_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            _err(f'No se pudo invocar {function_name}: {result.stderr.strip()}')
            return None
        try:
            response: dict[str, Any] = json.loads(out_path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            _err(f'Respuesta invalida de {function_name}: {exc}')
            return None

    return response


def _report_db_response(
    response: dict[str, Any] | None, *, ok_label: str
) -> int:
    """Imprime la respuesta de la Lambda `db` y devuelve el exit code.

    `ok_label` es el texto a mostrar cuando `status == 'ok'`. Returns 0 si
    la Lambda respondio ok, 1 en cualquier otro caso.
    """
    if response is None:
        return 1

    status = response.get('status')
    if status == 'ok':
        print(_c(GREEN, ok_label))
        for key in ('current', 'target'):
            if key in response and response[key] is not None:
                print(f'{DIM}  {key}: {response[key]}{NC}')
        for line in response.get('history', []):
            print(f'{DIM}  {line}{NC}')
        return 0

    # status 'error' | 'rejected' u otro.
    _err(response.get('error', f'la Lambda db respondio status={status!r}'))
    return 1


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
        # Neon branch via URL path o param. Ver .claude/rules/neon-management.md
        print(_c(YELLOW, f'Conectando a branch Neon: {branch}'))

    print(_c(CYAN, '$ psql <neon-url>'))
    result = subprocess.run(['psql', url], check=False)
    return result.returncode


def cmd_db_migrate(flags: dict[str, Any]) -> int:
    """Aplica las migraciones pendientes (`alembic upgrade`) via la Lambda db.

    `--target` opcional (default `head`). El schema lo definen los modelos
    SQLAlchemy de `common/db/`; las migraciones viven en
    `common/db/alembic/versions/`.
    """
    stage = flags.get('stage', 'local')
    target = flags.get('target', 'head')

    if flags.get('dry_run'):
        print(
            _c(
                YELLOW,
                f'[dry-run] invoke portfolio-db-{stage} '
                f'command=migrate target={target}',
            )
        )
        return 0

    print(_c(CYAN, f'$ invoke portfolio-db-{stage} command=migrate'))
    response = _invoke_db_lambda(stage, 'migrate', {'target': target})
    return _report_db_response(response, ok_label='OK  migraciones aplicadas')


def cmd_db_rollback(flags: dict[str, Any]) -> int:
    """Revierte migraciones (`alembic downgrade`) via la Lambda db.

    OPERACION DESTRUCTIVA: requiere `--confirm`. `--target` opcional
    (default `-1`, una migracion atras).
    """
    if not flags.get('confirm'):
        _err('--confirm requerido para rollback')
        return 2

    stage = flags.get('stage', 'local')
    target = flags.get('target', '-1')

    if flags.get('dry_run'):
        print(
            _c(
                YELLOW,
                f'[dry-run] invoke portfolio-db-{stage} '
                f'command=downgrade target={target}',
            )
        )
        return 0

    print(_c(CYAN, f'$ invoke portfolio-db-{stage} command=downgrade'))
    response = _invoke_db_lambda(
        stage, 'downgrade', {'target': target, 'confirm': True}
    )
    return _report_db_response(response, ok_label='OK  rollback aplicado')


def cmd_db_current(flags: dict[str, Any]) -> int:
    """Muestra la revision Alembic aplicada en la DB (via la Lambda db)."""
    stage = flags.get('stage', 'local')
    print(_c(CYAN, f'$ invoke portfolio-db-{stage} command=current'))
    response = _invoke_db_lambda(stage, 'current')
    return _report_db_response(response, ok_label='OK  revision actual')


def cmd_db_show_migrations(flags: dict[str, Any]) -> int:
    """Muestra el historial de migraciones Alembic (via la Lambda db)."""
    stage = flags.get('stage', 'local')
    print(_c(CYAN, f'$ invoke portfolio-db-{stage} command=show-migrations'))
    response = _invoke_db_lambda(stage, 'show-migrations')
    return _report_db_response(
        response, ok_label='OK  historial de migraciones'
    )


def cmd_db_seed(flags: dict[str, Any]) -> int:
    """Cargar data de prueba en Neon."""
    seed_script = _SERVERLESS_DIR / 'scripts' / 'seed_test_data.sql'
    if not seed_script.exists():
        _err(f'No existe: {seed_script}')
        print(
            f'{YELLOW}  Crear con sample data. '
            f'Ver .claude/docs/serverless-backend/{NC}'
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
