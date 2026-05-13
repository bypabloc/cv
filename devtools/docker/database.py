"""Database commands: psql shell, table inspection, seeds, full reset."""

from __future__ import annotations

from typing import Any

from docker._helpers import confirm_destructive
from docker._helpers import get_db_credentials
from docker.urls import print_service_urls
from shared.compose import compose_exec
from shared.compose import ensure_running
from shared.compose import run_compose
from shared.compose import wait_for_healthy
from shared.console import _err
from shared.console import _header
from shared.console import _info
from shared.console import _ok
from shared.console import _step


def cmd_db_shell(flags: dict[str, Any]) -> int:
    """Open an interactive psql shell."""
    env = flags['env']

    if not ensure_running(env):
        return 1

    creds = get_db_credentials(env)

    _info(f'Abriendo psql shell [{env}]...')
    result = compose_exec(
        env,
        'db',
        ['psql', '-U', creds['user'], '-d', creds['db']],
        interactive=True,
        timeout=None,
    )
    return result.returncode


def cmd_db_tables(flags: dict[str, Any]) -> int:
    """List all database tables.

    With ``--output=json`` emits a JSON array of qualified table names
    (``schema.table``) — useful for scripting bulk operations.
    """
    env = flags['env']
    output = flags.get('output', 'text')

    if not ensure_running(env):
        return 1

    creds = get_db_credentials(env)

    if output == 'json':
        import json

        # ORDER BY se aplica DENTRO de json_agg porque json no tiene operador
        # de orden (ORDER BY 1 sobre json_agg falla con 'could not identify
        # ordering operator for type json'). Subquery + ORDER BY t hace el
        # sort sobre el text antes de agregar.
        query = (
            'SELECT json_agg(t ORDER BY t) FROM ('
            "SELECT schemaname || '.' || tablename AS t FROM pg_tables "
            "WHERE schemaname NOT IN ('pg_catalog', 'information_schema')"
            ') sub;'
        )
        result = compose_exec(
            env,
            'db',
            [
                'psql',
                '-U',
                creds['user'],
                '-d',
                creds['db'],
                '-tAc',
                query,
            ],
            capture=True,
        )
        if result.returncode != 0:
            _err('Error listando tablas')
            return 1
        raw = (result.stdout or '').strip() or '[]'
        try:
            print(json.dumps(json.loads(raw), indent=2))
        except json.JSONDecodeError:
            print(raw)
        return 0

    _header(f'db tables [{env}]')
    result = compose_exec(
        env,
        'db',
        [
            'psql',
            '-U',
            creds['user'],
            '-d',
            creds['db'],
            '-c',
            r'\dt',
        ],
    )
    return result.returncode


def cmd_db_describe(flags: dict[str, Any]) -> int:
    """Describe a specific database table."""
    env = flags['env']
    subcommands = flags.get('subcommands', [])

    if not subcommands:
        _err('Se requiere el nombre de la tabla')
        _info('Uso: python devtools/run.py docker db-describe <tabla>')
        return 1

    table = subcommands[0]

    _header(f'db describe [{table}] [{env}]')

    if not ensure_running(env):
        return 1

    creds = get_db_credentials(env)

    result = compose_exec(
        env,
        'db',
        [
            'psql',
            '-U',
            creds['user'],
            '-d',
            creds['db'],
            '-c',
            f'\\d+ {table}',
        ],
    )
    return result.returncode


def cmd_db_count(flags: dict[str, Any]) -> int:
    """Show row counts for all tables, sorted descending.

    With ``--output=json`` emits ``{"schema.table": count, ...}``.
    """
    env = flags['env']
    output = flags.get('output', 'text')

    if not ensure_running(env):
        return 1

    creds = get_db_credentials(env)

    if output == 'json':
        import json

        # pg_stat_user_tables expone 'relname', no 'tablename' (que es la
        # columna en pg_tables). Mistake del primer intento de Fase 4.
        query = (
            "SELECT json_object_agg(schemaname || '.' || relname, n_live_tup) "
            'FROM pg_stat_user_tables;'
        )
        result = compose_exec(
            env,
            'db',
            [
                'psql',
                '-U',
                creds['user'],
                '-d',
                creds['db'],
                '-tAc',
                query,
            ],
            capture=True,
        )
        if result.returncode != 0:
            _err('Error obteniendo conteos')
            return 1
        raw = (result.stdout or '').strip() or '{}'
        try:
            print(json.dumps(json.loads(raw), indent=2))
        except json.JSONDecodeError:
            print(raw)
        return 0

    _header(f'db count [{env}]')
    # pg_stat_user_tables expone 'relname', no 'tablename' (que es la
    # columna de pg_tables). El JSON path ya estaba correcto; este text
    # path quedo con la columna mala desde Fase 4 y solo era visible
    # cuando alguien corria sin --output=json.
    query = (
        'SELECT schemaname, relname AS tablename, n_live_tup '
        'FROM pg_stat_user_tables '
        'ORDER BY n_live_tup DESC;'
    )
    result = compose_exec(
        env,
        'db',
        ['psql', '-U', creds['user'], '-d', creds['db'], '-c', query],
    )
    return result.returncode


def cmd_db_seed(flags: dict[str, Any]) -> int:
    """Run database seeds via Django management command.

    ``--dry-run`` imprime el comando sin ejecutarlo. Util para verificar
    que ``--clear`` no se cuela accidentalmente.
    """
    env = flags['env']
    dry_run = flags.get('dry_run', False)

    _header(f'db seed [{env}]' + (' [DRY-RUN]' if dry_run else ''))

    cmd = ['python', 'manage.py', 'seed_db', f'--env={env}']

    if flags.get('clear'):
        cmd.append('--clear')

    only = flags.get('only')
    if only:
        if isinstance(only, list):
            cmd.extend(['--only', *only])
        elif isinstance(only, str):
            cmd.extend(['--only', only])

    if dry_run:
        _step(f'compose_exec server "{" ".join(cmd)}"')
        _info('Sin cambios aplicados (--dry-run)')
        return 0

    if not ensure_running(env):
        return 1

    _step('Ejecutando seeds...')
    result = compose_exec(env, 'server', cmd)

    if result.returncode != 0:
        _err('Error ejecutando seeds')
        return 1

    _ok('Seeds aplicados')
    return 0


def cmd_db_reset(flags: dict[str, Any]) -> int:
    """Full database reset: destroy volumes, recreate, migrate, seed.

    Destructive: removes all database data. Asks for confirmation unless
    auto-piped (the input prompt fails closed in non-interactive contexts).
    ``--dry-run`` imprime los pasos sin ejecutar.
    """
    env = flags['env']
    dry_run = flags.get('dry_run', False)

    _header(f'db reset [{env}]' + (' [DRY-RUN]' if dry_run else ''))

    if dry_run:
        _step('1/5 docker compose down --volumes')
        _step('2/5 docker compose up -d')
        _step('3/5 wait_for_healthy(db, redis)')
        _step('4/5 manage.py migrate --noinput')
        _step('5/5 manage.py seed_db + createsuperuser --noinput')
        _info('Sin cambios aplicados (--dry-run)')
        return 0

    if not confirm_destructive(
        f'Se eliminara la base de datos completa en ambiente {env}.\n'
        '  Se perderan TODOS los datos y se recreara desde cero.'
    ):
        return 0

    _step('Paso 1/5: Deteniendo servicios y eliminando volumes...')
    result = run_compose(env, ['down', '--volumes'])
    if result.returncode != 0:
        _err('Error deteniendo servicios')
        return 1

    _step('Paso 2/5: Iniciando servicios...')
    result = run_compose(env, ['up', '-d'])
    if result.returncode != 0:
        _err('Error iniciando servicios')
        return 1

    _step('Paso 3/5: Esperando servicios saludables...')
    if not wait_for_healthy(env):
        return 1

    _step('Paso 4/5: Ejecutando migraciones...')
    result = compose_exec(
        env,
        'server',
        ['python', 'manage.py', 'migrate', '--noinput'],
    )
    if result.returncode != 0:
        _err('Error ejecutando migraciones')
        return 1

    _step('Paso 5/5: Ejecutando seeds y creando superusuario...')
    compose_exec(
        env,
        'server',
        ['python', 'manage.py', 'seed_db', f'--env={env}'],
    )
    compose_exec(
        env,
        'server',
        ['python', 'manage.py', 'createsuperuser', '--noinput'],
    )

    _ok('Database reset completado')
    print_service_urls(env)
    return 0
