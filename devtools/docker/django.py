"""Django management commands run inside the server container."""

from __future__ import annotations

from typing import Any

from shared.compose import compose_exec
from shared.compose import ensure_running
from shared.console import _err
from shared.console import _header
from shared.console import _info
from shared.console import _ok
from shared.console import _step
from shared.console import _warn


def cmd_migrate(flags: dict[str, Any]) -> int:
    """Run Django migrations."""
    env = flags['env']

    _header(f'django migrate [{env}]')

    if not ensure_running(env):
        return 1

    _step('Ejecutando migraciones...')
    result = compose_exec(
        env,
        'server',
        ['python', 'manage.py', 'migrate', '--noinput'],
    )

    if result.returncode != 0:
        _err('Error ejecutando migraciones')
        return 1

    _ok('Migraciones aplicadas')
    return 0


def cmd_makemigrations(flags: dict[str, Any]) -> int:
    """Generate Django migration files."""
    env = flags['env']
    subcommands = flags.get('subcommands', [])

    _header(f'django makemigrations [{env}]')

    if not ensure_running(env):
        return 1

    cmd = ['python', 'manage.py', 'makemigrations', '--noinput']
    if subcommands:
        cmd.extend(subcommands)

    _step('Generando migraciones...')
    result = compose_exec(env, 'server', cmd)

    if result.returncode != 0:
        _err('Error generando migraciones')
        return 1

    _ok('Migraciones generadas')
    return 0


def cmd_createsuperuser(flags: dict[str, Any]) -> int:
    """Create Django superuser using environment variables.

    Relies on DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL and
    DJANGO_SUPERUSER_PASSWORD being set in the env file. ``--noinput``
    exits 1 if the user already exists; we treat that as success.
    """
    env = flags['env']

    _header(f'django createsuperuser [{env}]')

    if not ensure_running(env):
        return 1

    _step('Creando superusuario...')
    result = compose_exec(
        env,
        'server',
        ['python', 'manage.py', 'createsuperuser', '--noinput'],
    )

    if result.returncode != 0:
        _warn(
            'createsuperuser retorno codigo distinto de 0. '
            'Puede que el usuario ya exista.'
        )
        return 0

    _ok('Superusuario creado')
    return 0


def cmd_manage(flags: dict[str, Any]) -> int:
    """Pass-through to Django manage.py.

    Para flags Django (que el validador del CLI desconoce), separar con
    ``--`` POSIX. Ej: ``docker manage migrate -- --plan --verbosity=2``.
    Sin separador, el CLI intercepta los flags y rechaza con un hint.
    """
    env = flags['env']
    subcommands = flags.get('subcommands', [])

    if not subcommands:
        _err('Se requiere un comando de manage.py')
        _info(
            'Uso: python devtools/run.py docker manage <comando> '
            '[-- --flag-django=value]',
        )
        return 1

    if not ensure_running(env):
        return 1

    cmd = ['python', 'manage.py', *subcommands]

    _info(f'manage.py {" ".join(subcommands)}')
    result = compose_exec(env, 'server', cmd)
    return result.returncode
