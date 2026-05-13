"""Project setup and clean commands.

``setup`` is the first-time bootstrap: build images, start services,
migrate, optionally seed and create a superuser, sync ``server/.venv`` for
VS Code intellisense. ``clean`` is the destructive teardown that removes
containers, images and volumes for the current environment.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from docker._helpers import confirm_destructive
from docker.urls import print_service_urls
from shared.compose import compose_exec
from shared.compose import run_cmd
from shared.compose import run_compose
from shared.compose import wait_for_healthy
from shared.console import _err
from shared.console import _header
from shared.console import _info
from shared.console import _ok
from shared.console import _step
from shared.console import _warn
from shared.paths import DOCKER_DIR
from shared.paths import PROJECT_ROOT
from shared.project_config import CONTAINER_PREFIX


def cmd_setup(flags: dict[str, Any]) -> int:
    """Full initial project setup: build, start, migrate, seed, superuser.

    Counts steps dynamically (--no-seed and --no-superuser shorten the
    sequence). The final step syncs ``server/.venv`` on the host so VS
    Code Pylance has a real Python interpreter to inspect even though the
    runtime lives in Docker.
    """
    env = flags['env']
    no_seed = flags.get('no_seed', False)
    no_superuser = flags.get('no_superuser', False)

    _header(f'Setup completo [{env}]')

    env_file = DOCKER_DIR / 'env' / f'.{env}'
    if not env_file.exists():
        _err(f'Archivo de entorno no encontrado: {env_file}')
        _info(
            f'Copiar el archivo de ejemplo:\n'
            f'  cp {DOCKER_DIR / "env" / ".example"} {env_file}'
        )
        return 1

    total_steps = 6
    if no_seed:
        total_steps -= 1
    if no_superuser:
        total_steps -= 1
    step = 0

    step += 1
    _step(f'Paso {step}/{total_steps}: Construyendo imágenes...')
    result = run_compose(env, ['build'], timeout=600)
    if result.returncode != 0:
        _err('Error construyendo imágenes')
        return 1

    step += 1
    _step(f'Paso {step}/{total_steps}: Iniciando servicios...')
    result = run_compose(env, ['up', '-d'])
    if result.returncode != 0:
        _err('Error iniciando servicios')
        return 1

    step += 1
    _step(f'Paso {step}/{total_steps}: Esperando servicios saludables...')
    if not wait_for_healthy(env):
        return 1

    step += 1
    _step(f'Paso {step}/{total_steps}: Ejecutando migraciones...')
    result = compose_exec(
        env,
        'server',
        ['python', 'manage.py', 'migrate', '--noinput'],
    )
    if result.returncode != 0:
        _err('Error ejecutando migraciones')
        return 1

    if not no_seed:
        step += 1
        _step(f'Paso {step}/{total_steps}: Ejecutando seeds...')
        compose_exec(
            env,
            'server',
            ['python', 'manage.py', 'seed_db', f'--env={env}'],
        )

    if not no_superuser:
        step += 1
        _step(f'Paso {step}/{total_steps}: Creando superusuario...')
        compose_exec(
            env,
            'server',
            ['python', 'manage.py', 'createsuperuser', '--noinput'],
        )

    step += 1
    _setup_server_venv_step(step, total_steps)

    print_service_urls(env)
    _ok('Setup completado')
    return 0


def _setup_server_venv_step(step: int, total_steps: int) -> None:
    """Sync server/.venv on the host for VS Code intellisense.

    Failure here is non-fatal: the project still runs via Docker.
    """
    _step(
        f'Paso {step}/{total_steps}: Sincronizando server/.venv del host '
        '(intellisense de VS Code)...'
    )
    if _ensure_server_venv() != 0:
        _warn(
            'No se pudo crear server/.venv. El proyecto sigue funcionando '
            'via Docker; solo se pierde intellisense local en VS Code.'
        )


def _ensure_server_venv() -> int:
    """Sync ``server/.venv`` on the host with ``uv sync --frozen``.

    The container runs Python 3.14 but VS Code Pylance needs a venv it can
    inspect locally. ``uv sync`` reads ``server/pyproject.toml`` +
    ``server/uv.lock`` and produces a venv at ``server/.venv`` matching the
    requires-python pin. Falls back gracefully when uv is missing.

    Returns 0 on success, 1 on failure.
    """
    server_dir = PROJECT_ROOT / 'server'
    pyproject = server_dir / 'pyproject.toml'

    if not pyproject.exists():
        _warn(
            'server/pyproject.toml no existe — saltando sync de venv local',
        )
        return 1

    uv_bin = shutil.which('uv')
    if uv_bin is None:
        _err(
            'uv no esta en PATH. Instalalo con:\n'
            '  curl -LsSf https://astral.sh/uv/install.sh | sh',
        )
        return 1

    _info('Sincronizando server/.venv con uv sync --frozen...')
    result = subprocess.run(  # noqa: S603
        [uv_bin, 'sync', '--frozen', '--project', str(server_dir)],
        check=False,
        timeout=300,
    )
    if result.returncode != 0:
        _err('uv sync fallo en server/')
        return 1

    _ok(
        'server/.venv listo (solo intellisense — runtime sigue en Docker)',
    )
    return 0


def cmd_clean(flags: dict[str, Any]) -> int:
    """Remove all containers, images and volumes for the current environment.

    Destructive: requires explicit confirmation. Filters by the project's
    container prefix so other compose projects on the same Docker daemon
    are untouched. ``--dry-run`` imprime los pasos sin ejecutar.
    """
    from docker.cache import _clear_pycache_local

    env = flags['env']
    dry_run = flags.get('dry_run', False)

    _header(f'docker clean [{env}]' + (' [DRY-RUN]' if dry_run else ''))

    if dry_run:
        _step('1/4 docker compose down --volumes --rmi all --remove-orphans')
        _step(
            f'2/4 docker rm -f <containers con prefix {CONTAINER_PREFIX}- '
            f'sufijo -{env}>',
        )
        _step('3/4 docker volume rm <dangling con prefix>')
        _step('4/4 Limpiar __pycache__ locales')
        _info('Sin cambios aplicados (--dry-run)')
        return 0

    if not confirm_destructive(
        f'Se eliminaran TODOS los containers, imágenes y volumes\n'
        f'  con prefijo "{CONTAINER_PREFIX}" del ambiente {env}.\n'
        f'  Esto incluye la base de datos y datos de cache.'
    ):
        return 0

    _step('Paso 1/4: Deteniendo y eliminando servicios...')
    run_compose(
        env,
        ['down', '--volumes', '--rmi', 'all', '--remove-orphans'],
    )

    _step('Paso 2/4: Eliminando containers huerfanos...')
    container_prefix = f'{CONTAINER_PREFIX}-'
    result = run_cmd(
        ['docker', 'ps', '-a', '--format', '{{.Names}}'],
        capture=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        containers = [
            name.strip()
            for name in result.stdout.strip().split('\n')
            if name.strip().startswith(container_prefix)
            and name.strip().endswith(f'-{env}')
        ]
        if containers:
            run_cmd(['docker', 'rm', '-f', *containers])
            _info(f'Eliminados {len(containers)} containers')
        else:
            _info('No se encontraron containers huerfanos')

    _step('Paso 3/4: Limpiando volumes huerfanos...')
    result = run_cmd(
        ['docker', 'volume', 'ls', '--filter', 'dangling=true', '-q'],
        capture=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        volumes = result.stdout.strip().split('\n')
        gm_volumes = [
            v.strip()
            for v in volumes
            if v.strip() and CONTAINER_PREFIX in v.strip()
        ]
        if gm_volumes:
            run_cmd(['docker', 'volume', 'rm', *gm_volumes])
            _info(f'Eliminados {len(gm_volumes)} volumes')

    _step('Paso 4/4: Limpiando __pycache__ locales...')
    _clear_pycache_local()

    _ok('Limpieza completada')
    return 0
