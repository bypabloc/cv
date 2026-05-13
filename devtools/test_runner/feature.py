"""Feature execution helpers (Playwright para dashboard/landing, pytest para server).

Mayo 2026: reemplaza al historico ``e2e.py``. Cada modulo tiene su
propio ``--type=feature``:

  - ``--module=dashboard --type=feature`` -> servicio dashboard-feature (Playwright)
  - ``--module=landing --type=feature``   -> servicio landing-feature (Playwright)
  - ``--module=server --type=feature``    -> pytest -m feature contra
                                              tests/feature/ con seed_db

Para los containers de Playwright esperamos el sentinel
``/tmp/.feature-ready`` (creado por ``docker/scripts/feature-entrypoint.sh``).
El wait helper aborta si el container muere durante setup.
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


_FEATURE_READY_TIMEOUT_DEFAULT = 600
_FEATURE_READY_POLL_INTERVAL = 2
_FEATURE_READY_PROGRESS_INTERVAL = 30


def _feature_service_for(module: str) -> str:
    """Map module to its compose service name.

    Portfolio: el servicio Playwright es unico (``feature``) y testea
    todas las apps Astro a traves de nginx. No hay containers feature
    por-app como en el template fuente.
    """
    if module == 'feature':
        return 'feature'
    raise ValueError(
        f'Modulo {module!r} no tiene servicio Playwright asociado. '
        'Solo --module=feature soporta Playwright en portfolio.',
    )


def _container_alive(docker_bin: str, container: str) -> bool:
    """True if the container is running (not exited/restarting)."""
    inspect = subprocess.run(  # noqa: S603
        [
            docker_bin,
            'inspect',
            '-f',
            '{{.State.Running}}',
            container,
        ],
        capture_output=True,
        check=False,
        timeout=5,
        text=True,
    )
    return inspect.returncode == 0 and inspect.stdout.strip() == 'true'


def _wait_feature_ready(env: str, module: str, timeout_s: int) -> bool:
    """Wait until the feature container creates ``/tmp/.feature-ready``."""
    docker_bin = shutil.which('docker') or 'docker'
    service = _feature_service_for(module)
    container = f'{PROJECT_NAME}-{service}-{env}'

    start = time.time()
    next_progress = start + _FEATURE_READY_PROGRESS_INTERVAL
    deadline = start + timeout_s

    while time.time() < deadline:
        check = subprocess.run(  # noqa: S603
            [
                docker_bin,
                'exec',
                container,
                'sh',
                '-c',
                'test -f /tmp/.feature-ready',
            ],
            capture_output=True,
            check=False,
            timeout=5,
        )
        if check.returncode == 0:
            elapsed = int(time.time() - start)
            _ok(f'Feature container ({module}) listo en {elapsed}s')
            return True

        if not _container_alive(docker_bin, container):
            _err(
                f'Feature container {container} murio durante setup '
                f'(revisa logs: docker logs {container})',
            )
            return False

        if time.time() >= next_progress:
            elapsed = int(time.time() - start)
            _step(
                f'Esperando feature container ({module})... '
                f'({elapsed}s / max {timeout_s}s)',
            )
            next_progress = time.time() + _FEATURE_READY_PROGRESS_INTERVAL

        time.sleep(_FEATURE_READY_POLL_INTERVAL)

    _err(
        f'Feature container ({module}) no quedo listo en {timeout_s}s. '
        f'Aumentar via FEATURE_READY_TIMEOUT (env var).',
    )
    return False


def ensure_feature_running(env: str, module: str) -> bool:
    """Bring up the on-demand feature service and wait until it is ready.

    First invocation can take several minutes (installs Chromium + WebKit
    + pnpm). Timeout configurable via ``FEATURE_READY_TIMEOUT`` env var.
    """
    service = _feature_service_for(module)
    if is_service_running(env, service):
        return True

    _step(f'Levantando servicio {service}...')
    cmd = [
        *get_compose_cmd(env),
        '--profile',
        'feature',
        'up',
        '-d',
        service,
    ]
    result = run_cmd(cmd, capture=True, check=False, timeout=120)
    if result.returncode != 0:
        _err(f'No se pudo levantar el servicio {service}')
        return False

    timeout_s = int(
        os.environ.get(
            'FEATURE_READY_TIMEOUT',
            _FEATURE_READY_TIMEOUT_DEFAULT,
        ),
    )
    return _wait_feature_ready(env, module, timeout_s)


def run_feature(
    *,
    env: str,
    module: str,
    verbose: bool,
    quiet: bool,
    project: str = '',
    screenshots: bool = False,
    shard: int | None = None,
    shard_total: int | None = None,
    fail_on_flaky: bool = False,
) -> int:
    """Run feature tests via Docker (Playwright).

    Parameters
    ----------
    module : str
        Either ``app`` or ``landing``. Determines the compose service.
    project : str
        Playwright project filter (desktop-chromium, desktop-webkit, etc.).
    shard / shard_total : int | None
        1-based shard index + total, yields ``--shard=N/M`` for CI parallelism.
    fail_on_flaky : bool
        Pass ``--fail-on-flaky-tests`` to Playwright (CI mode).
    """
    if not ensure_feature_running(env, module):
        return 1

    service = _feature_service_for(module)
    _step(f'Ejecutando feature tests ({module})...')

    # Llamar playwright directo (no pnpm exec) para evitar que pnpm intente
    # auto-install al detectar workspace en /app. tests/feature/ tiene su
    # propio package.json aislado con --ignore-workspace.
    cmd = ['./node_modules/.bin/playwright', 'test']
    if project:
        cmd.append(f'--project={project}')
    if shard is not None and shard_total is not None:
        cmd.append(f'--shard={shard}/{shard_total}')
    if fail_on_flaky:
        cmd.append('--fail-on-flaky-tests')

    spawn_env: dict[str, str] = {'CI': 'true'}
    if screenshots:
        spawn_env['TAKE_SCREENSHOTS'] = '1'

    result = compose_exec(
        env,
        service,
        cmd,
        timeout=600,
        capture=quiet,
        extra_env=spawn_env,
    )

    if result.returncode != 0:
        if quiet and hasattr(result, 'stdout') and result.stdout:
            print(result.stdout)
        _err(f'Feature tests ({module}) fallaron')
        return 1

    _ok(f'Feature tests ({module}) pasaron')
    return 0
