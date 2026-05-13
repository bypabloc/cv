"""Recovery-flavour lifecycle commands: rebuild and refresh.

Both are multi-step orchestrations that lifecyle's ``up``/``down``/``build``
do not need to import: rebuild does down + build --no-cache + up, and
refresh does down + cache clear + up + post-migrations. Kept apart so
``lifecycle.py`` stays under 300 lines.
"""

from __future__ import annotations

from typing import Any

from docker._helpers import resolve_profile
from docker.urls import print_service_urls
from shared.compose import compose_exec
from shared.compose import run_compose
from shared.compose import wait_for_healthy
from shared.console import _err
from shared.console import _header
from shared.console import _info
from shared.console import _ok
from shared.console import _step


def cmd_rebuild(flags: dict[str, Any]) -> int:
    """Full clean rebuild.

    Modes:
    - Default (no ``--service``): down + build --no-cache + up -d for the
      whole compose stack.
    - With ``--service=<name>``: stop+remove only that container, rebuild
      its image with ``--no-cache``, then start it back.

    With ``--dry-run`` prints the steps without executing anything.
    """
    env = flags['env']
    service = flags.get('service')
    profile = resolve_profile(flags)
    dry_run = flags.get('dry_run', False)

    target = service or 'all services'
    profile_label = f' (profile={profile})' if profile else ''
    _header(
        f'docker rebuild [{env}] {target}{profile_label}'
        + (' [DRY-RUN]' if dry_run else ''),
    )

    if dry_run:
        return _print_rebuild_plan(env, service=service, profile=profile)

    if service:
        _step('Paso 1/3: Deteniendo y removiendo container...')
        result = run_compose(env, ['rm', '-fsv', service], profile=profile)
        if result.returncode != 0:
            _info('Container no existia, continuando.')

        _step(f'Paso 2/3: Reconstruyendo imagen "{service}" (sin cache)...')
        result = run_compose(
            env,
            ['build', '--no-cache', service],
            timeout=600,
            profile=profile,
        )
        if result.returncode != 0:
            _err('Error construyendo imagen')
            return 1

        _step(f'Paso 3/3: Iniciando servicio "{service}"...')
        result = run_compose(env, ['up', '-d', service], profile=profile)
        if result.returncode != 0:
            _err('Error iniciando servicio')
            return 1

        _ok(f'Rebuild de "{service}" completado')
        return 0

    _step('Paso 1/3: Deteniendo servicios...')
    result = run_compose(env, ['down'])
    if result.returncode != 0:
        _err('Error deteniendo servicios')
        return 1

    _step('Paso 2/3: Reconstruyendo imagenes (sin cache)...')
    result = run_compose(env, ['build', '--no-cache'], timeout=600)
    if result.returncode != 0:
        _err('Error construyendo imagenes')
        return 1

    _step('Paso 3/3: Iniciando servicios...')
    result = run_compose(env, ['up', '-d'])
    if result.returncode != 0:
        _err('Error iniciando servicios')
        return 1

    print_service_urls(env)
    _ok('Rebuild completado')
    return 0


def cmd_refresh(flags: dict[str, Any]) -> int:
    """Refresh: down + optional cache clear + up + post-migrations.

    Supports ``--keep-volumes`` to preserve DB data and ``--skip-cache``
    to skip the local pycache cleanup. ``--dry-run`` imprime los pasos.
    """
    from docker.cache import _clear_pycache_local

    env = flags['env']
    keep_volumes = flags.get('keep_volumes', False)
    skip_cache = flags.get('skip_cache', False)
    dry_run = flags.get('dry_run', False)

    _header(
        f'docker refresh [{env}]' + (' [DRY-RUN]' if dry_run else ''),
    )

    if dry_run:
        return _print_refresh_plan(
            env,
            keep_volumes=keep_volumes,
            skip_cache=skip_cache,
        )

    down_args = ['down']
    if not keep_volumes:
        down_args.append('--volumes')

    _step('Paso 1/3: Deteniendo servicios...')
    result = run_compose(env, down_args)
    if result.returncode != 0:
        _err('Error deteniendo servicios')
        return 1

    if not skip_cache:
        _step('Paso 2/3: Limpiando caches...')
        _clear_pycache_local()
    else:
        _step('Paso 2/3: Omitiendo limpieza de cache (--skip-cache)')

    _step('Paso 3/3: Iniciando servicios...')
    result = run_compose(env, ['up', '-d', '--build'])
    if result.returncode != 0:
        _err('Error iniciando servicios')
        return 1

    if not keep_volumes and wait_for_healthy(env):
        _step('Ejecutando migraciones post-refresh...')
        compose_exec(
            env,
            'server',
            ['python', 'manage.py', 'migrate', '--noinput'],
        )

    print_service_urls(env)
    _ok('Refresh completado')
    return 0


def _print_rebuild_plan(
    env: str,
    *,
    service: str | None,
    profile: str | None,
) -> int:
    """Print rebuild steps without executing anything."""
    if service:
        _step(f'1/3 docker compose rm -fsv {service}')
        _step(f'2/3 docker compose build --no-cache {service}')
        _step(f'3/3 docker compose up -d {service}')
        if profile:
            _info(f'(con profile={profile})')
    else:
        _step('1/3 docker compose down')
        _step('2/3 docker compose build --no-cache')
        _step('3/3 docker compose up -d')
    _info('Sin cambios aplicados (--dry-run)')
    return 0


def _print_refresh_plan(
    env: str,
    *,
    keep_volumes: bool,
    skip_cache: bool,
) -> int:
    """Print refresh steps without executing anything."""
    down_args = ['down']
    if not keep_volumes:
        down_args.append('--volumes')
    _step(f'1/3 docker compose {" ".join(down_args)}')
    if not skip_cache:
        _step('2/3 Limpiar __pycache__ del proyecto')
    else:
        _step('2/3 Saltar limpieza de cache (--skip-cache)')
    _step('3/3 docker compose up -d --build')
    if not keep_volumes:
        _info('Despues de healthy: manage.py migrate --noinput')
    _info('Sin cambios aplicados (--dry-run)')
    return 0
