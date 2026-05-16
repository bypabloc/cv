"""Docker lifecycle commands: up, down, build, logs, shell, exec, ps, restart.

These commands manipulate the container lifecycle but never run code
inside existing containers (that lives in ``quality.py``).
``cmd_rebuild`` and ``cmd_refresh`` live in ``lifecycle_recovery.py``
because they are multi-step orchestrations.
"""

from __future__ import annotations

import sys
from typing import Any

from docker._helpers import confirm_destructive
from docker._helpers import resolve_profile
from docker.urls import print_service_urls
from shared.compose import compose_exec
from shared.compose import ensure_running
from shared.compose import run_compose
from shared.console import _err
from shared.console import _header
from shared.console import _info
from shared.console import _ok
from shared.console import _step
from shared.paths import DOCKER_DIR


def cmd_up(flags: dict[str, Any]) -> int:
    """Start docker compose services.

    With ``--service=<name>`` only that service (and its dependencies) is
    started. Profiles auto-resolve from the service name when known
    (see ``flags.PROFILE_SERVICES``) or via ``--profile=<name>``.
    """
    env = flags['env']
    service = flags.get('service')
    profile = resolve_profile(flags)

    target = service or 'todos los servicios'
    profile_label = f' (profile={profile})' if profile else ''
    _header(f'docker up [{env}] {target}{profile_label}')

    compose_file = DOCKER_DIR / 'docker-compose' / f'{env}.yml'
    if not compose_file.exists():
        _err(f'Compose file no encontrado: {compose_file}')
        return 1

    args = ['up']

    if flags.get('detach', True):
        args.append('-d')

    if flags.get('build'):
        args.append('--build')

    if service:
        args.append(service)

    _step(f'Iniciando {target} en ambiente {env}...')
    result = run_compose(env, args, profile=profile)

    if result.returncode != 0:
        _err('Error iniciando servicios')
        return 1

    if flags.get('detach', True) and not service:
        print_service_urls(env)

    _ok('Servicios iniciados')
    return 0


def cmd_down(flags: dict[str, Any]) -> int:
    """Stop docker compose services."""
    env = flags['env']

    _header(f'docker down [{env}]')

    args = ['down']

    if flags.get('volumes'):
        if not confirm_destructive(
            'Se eliminaran todos los volumes (incluye datos de PostgreSQL).'
        ):
            return 0
        args.append('--volumes')

    _step('Deteniendo servicios...')
    result = run_compose(env, args)

    if result.returncode != 0:
        _err('Error deteniendo servicios')
        return 1

    _ok('Servicios detenidos')
    return 0


def cmd_build(flags: dict[str, Any]) -> int:
    """Build docker compose images.

    Supports building all services (default), a single service via
    ``--service=<name>``, or a profile-gated service via ``--profile=<name>``.
    """
    env = flags['env']
    service = flags.get('service')
    profile = resolve_profile(flags)

    target = service or 'all services'
    profile_label = f' (profile={profile})' if profile else ''
    _header(f'docker build [{env}] {target}{profile_label}')

    args = ['build']

    if flags.get('no_cache'):
        args.append('--no-cache')

    if service:
        args.append(service)

    _step('Construyendo imágenes...')
    result = run_compose(env, args, timeout=600, profile=profile)

    if result.returncode != 0:
        _err('Error construyendo imágenes')
        return 1

    _ok('Imágenes construidas')
    return 0


def cmd_logs(flags: dict[str, Any]) -> int:
    """Show service logs."""
    env = flags['env']
    subcommands = flags.get('subcommands', [])

    _header(f'docker logs [{env}]')

    tail = flags.get('tail', 50)
    follow = flags.get('follow', False)

    args = ['logs', f'--tail={tail}']

    if follow:
        args.append('--follow')

    if subcommands:
        args.extend(subcommands)

    _step(f'Mostrando logs (tail={tail}, follow={follow})...')
    result = run_compose(env, args, timeout=None if follow else 60)

    return result.returncode


def cmd_shell(flags: dict[str, Any]) -> int:
    """Open an interactive bash shell in the server container."""
    env = flags['env']

    if not ensure_running(env):
        return 1

    _info(f'Abriendo shell en server [{env}]...')
    result = compose_exec(
        env,
        'server',
        ['bash'],
        interactive=True,
        timeout=None,
    )
    return result.returncode


def cmd_exec(flags: dict[str, Any]) -> int:
    """Run an arbitrary command in a container.

    Convencion: el comando del subproceso va después del separador POSIX
    ``--`` para que el validador del CLI no rechace los flags. Ej:
    ``docker exec --target=dashboard -- pnpm install`` o
    ``docker exec -- python manage.py shell``.
    """
    env = flags['env']
    target = flags.get('target', 'server')
    subcommands = flags.get('subcommands', [])

    if not subcommands:
        _err('Se requiere un comando.')
        _info(
            'Uso: python devtools/run.py docker exec '
            '[--target=<servicio>] -- <comando> [args...]',
        )
        return 1

    if not ensure_running(env):
        return 1

    _info(f'Ejecutando en {target} [{env}]: {" ".join(subcommands)}')
    result = compose_exec(env, target, subcommands)
    return result.returncode


def cmd_ps(flags: dict[str, Any]) -> int:
    """List running containers.

    With ``--output=json`` emits a single JSON array of container objects.
    ``docker compose ps --format=json`` natively emits NDJSON (one object
    per line) which breaks ``json.load(sys.stdin)`` — we wrap it so the
    output matches the convention used by ``db-tables`` / ``db-count`` /
    ``cache-status`` (one parseable JSON document per command).
    """
    import json

    env = flags['env']
    output = flags.get('output', 'text')

    if output == 'json':
        result = run_compose(env, ['ps', '--format', 'json'], capture=True)
        if result.returncode != 0:
            _err('Error listando containers')
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return result.returncode
        raw = (result.stdout or '').strip()
        if not raw:
            print('[]')
            return 0
        # docker compose ps emite NDJSON (un objeto por linea). Versiones mas
        # nuevas reportan también array JSON; aceptamos ambos. Detectamos el
        # caso array via el primer carácter no-whitespace para evitar el
        # try/except/pass que Ruff S110 marca como anti-patron.
        if raw.lstrip().startswith('['):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                _err(f'docker compose ps emitio JSON inválido: {exc}')
                return 1
            print(json.dumps(parsed, indent=2))
            return 0

        items = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                _err(f'Linea de docker compose ps no parseable: {line[:80]}')
                return 1
        print(json.dumps(items, indent=2))
        return 0

    _header(f'docker ps [{env}]')
    result = run_compose(env, ['ps'])
    return result.returncode


def cmd_restart(flags: dict[str, Any]) -> int:
    """Restart docker compose services."""
    env = flags['env']
    subcommands = flags.get('subcommands', [])

    _header(f'docker restart [{env}]')

    args = ['restart']
    if subcommands:
        args.extend(subcommands)

    _step('Reiniciando servicios...')
    result = run_compose(env, args)

    if result.returncode != 0:
        _err('Error reiniciando servicios')
        return 1

    _ok('Servicios reiniciados')
    return 0
