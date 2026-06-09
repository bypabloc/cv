"""Lifecycle del container Docker `e2e` (Playwright + Python 3.14).

Analogo a `test_runner/feature.py` pero para el container `e2e`: lo levanta
on-demand (profile `e2e`), espera el sentinel `/tmp/.e2e-ready` (creado por
`docker/scripts/e2e-entrypoint.sh`) y corre pytest DENTRO del container con
`compose_exec`. El container corre contra el backend DESPLEGADO (dev):
solo necesita salida a internet + acceso a SSM/Neon (no el stack de apps).

Solo lo usan los modulos browser (`admin`, `app`). El modulo `api` corre
con httpx puro y NO necesita container.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time

from shared.compose import compose_exec
from shared.compose import get_compose_cmd
from shared.compose import is_service_running
from shared.compose import run_cmd
from shared.console import _err
from shared.console import _ok
from shared.console import _step
from shared.project_config import PROJECT_NAME


_E2E_SERVICE = 'e2e'
_E2E_PROFILE = 'e2e'
# Sentinel DENTRO del container (no es un temp file del host): lo crea
# e2e-entrypoint.sh cuando el container queda ready. Mismo patron que el
# `/tmp/.feature-ready` del container `feature`.
_E2E_SENTINEL = '/tmp/.e2e-ready'  # noqa: S108 -- path interno del container
# Workdir del container: el repo se bind-montea en /app, los tests viven en
# /app/tests. Pytest corre desde ahi (su pyproject.toml define testpaths).
_E2E_WORKDIR = '/app/tests'

_READY_TIMEOUT_DEFAULT = 600
_READY_POLL_INTERVAL = 2
_READY_PROGRESS_INTERVAL = 30


def _container_name(env: str) -> str:
    """Nombre del container `e2e` para un env (portfolio-e2e-<env>)."""
    return f'{PROJECT_NAME}-{_E2E_SERVICE}-{env}'


def _container_alive(docker_bin: str, container: str) -> bool:
    """True si el container esta corriendo (no exited/restarting)."""
    inspect = subprocess.run(  # noqa: S603
        [docker_bin, 'inspect', '-f', '{{.State.Running}}', container],
        capture_output=True,
        check=False,
        timeout=5,
        text=True,
    )
    return inspect.returncode == 0 and inspect.stdout.strip() == 'true'


def _wait_e2e_ready(env: str, timeout_s: int) -> bool:
    """Espera a que el container `e2e` cree `/tmp/.e2e-ready`."""
    docker_bin = shutil.which('docker') or 'docker'
    container = _container_name(env)

    start = time.time()
    next_progress = start + _READY_PROGRESS_INTERVAL
    deadline = start + timeout_s

    while time.time() < deadline:
        check = subprocess.run(  # noqa: S603
            [
                docker_bin,
                'exec',
                container,
                'sh',
                '-c',
                f'test -f {_E2E_SENTINEL}',
            ],
            capture_output=True,
            check=False,
            timeout=5,
        )
        if check.returncode == 0:
            elapsed = int(time.time() - start)
            _ok(f'Container e2e listo en {elapsed}s')
            return True

        if not _container_alive(docker_bin, container):
            _err(
                f'Container {container} murio durante setup '
                f'(revisa logs: docker logs {container})',
            )
            return False

        if time.time() >= next_progress:
            elapsed = int(time.time() - start)
            _step(
                f'Esperando container e2e... ({elapsed}s / max {timeout_s}s)',
            )
            next_progress = time.time() + _READY_PROGRESS_INTERVAL

        time.sleep(_READY_POLL_INTERVAL)

    _err(
        f'Container e2e no quedo listo en {timeout_s}s. '
        f'Aumentar via E2E_READY_TIMEOUT (env var).',
    )
    return False


def ensure_e2e_container(env: str) -> bool:
    """Levanta el container `e2e` on-demand y espera a que quede ready.

    El primer arranque puede tardar varios minutos (instala browsers +
    deps). Timeout configurable via `E2E_READY_TIMEOUT` (env var).
    """
    if is_service_running(env, _E2E_SERVICE):
        return True

    _step('Levantando container e2e...')
    cmd = [
        *get_compose_cmd(env, profile=_E2E_PROFILE),
        'up',
        '-d',
        _E2E_SERVICE,
    ]
    result = run_cmd(cmd, capture=True, check=False, timeout=120)
    if result.returncode != 0:
        _err('No se pudo levantar el container e2e')
        return False

    timeout_s = int(
        os.environ.get('E2E_READY_TIMEOUT', _READY_TIMEOUT_DEFAULT),
    )
    return _wait_e2e_ready(env, timeout_s)


def run_pytest_in_container(
    *,
    env: str,
    pytest_args: list[str],
    quiet: bool,
    extra_env: dict[str, str] | None = None,
) -> int:
    """Corre `pytest <args>` DENTRO del container `e2e` (browser modules).

    Devuelve el exit code de pytest (0 = todos PASS, !=0 = algun FAIL).
    El container ya debe estar ready (`ensure_e2e_container`).
    """
    cmd = ['devtools/.venv/bin/python', '-m', 'pytest', *pytest_args]
    result = compose_exec(
        env,
        _E2E_SERVICE,
        cmd,
        timeout=900,
        capture=quiet,
        workdir=_E2E_WORKDIR,
        extra_env=extra_env or {},
    )
    if result.returncode != 0 and quiet and getattr(result, 'stdout', None):
        print(result.stdout)
    return result.returncode
