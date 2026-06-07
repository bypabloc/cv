"""Docker Compose orchestration helpers shared by devtools scripts.

Wraps ``docker compose`` invocations with consistent defaults: working
directory, env-file resolution, capture/interactive flags. Centralizing
these helpers here means ``docker``, ``test_runner``, ``e2e`` and the git
hooks all use the same compose semantics without importing from each
other.

Use ``run_compose`` for plain compose commands and ``compose_exec`` to
run a process inside an already-running service container. ``ensure_running``
auto-starts services if they are down.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Any

from shared.console import DIM
from shared.console import _c
from shared.console import err
from shared.console import info
from shared.console import ok
from shared.console import warn
from shared.paths import DOCKER_DIR
from shared.paths import PROJECT_ROOT
from shared.project_config import PROJECT_NAME


HEALTH_CHECK_TIMEOUT = 60
HEALTH_CHECK_INTERVAL = 3


def get_compose_cmd(env: str, profile: str | None = None) -> list[str]:
    """Build the base ``docker compose`` command for an environment.

    Args:
        env: Environment name (local, dev, test, prod).
        profile: Optional compose profile name (e.g., ``e2e`` for on-demand
            services gated behind ``profiles: [e2e]`` in the compose file).

    Returns:
        List of command tokens for subprocess.
    """
    compose_file = DOCKER_DIR / 'docker-compose' / f'{env}.yml'

    cmd = [
        'docker',
        'compose',
        '--project-name',
        PROJECT_NAME,
        '-f',
        str(compose_file),
    ]

    if profile:
        cmd.extend(['--profile', profile])

    # Env vars repartidas en 3 archivos por categoria de sensibilidad:
    #   client  -> valores publicos (PUBLIC_*, puertos, dominios)
    #   server  -> config del backend + secretos de runtime
    #   dev-cli -> credenciales del devtools CLI
    # docker compose fusiona multiples --env-file en orden; las categorias
    # no comparten nombres de variable, asi que no hay colision.
    for category in ('client', 'server', 'dev-cli'):
        env_file = DOCKER_DIR / 'env' / category / f'.{env}'
        if env_file.exists():
            cmd.extend(['--env-file', str(env_file)])

    return cmd


def run_cmd(
    cmd: list[str],
    capture: bool = False,
    check: bool = False,
    cwd: str | None = None,
    timeout: int | None = 300,
    interactive: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Execute a subprocess command with devtools defaults.

    UID/GID are exported so containers see the host user (avoids root-owned
    files in bind mounts). Working directory defaults to the project root.
    """
    env = os.environ.copy()
    env.setdefault('UID', str(os.getuid()))
    env.setdefault('GID', str(os.getgid()))

    kwargs: dict[str, Any] = {
        'cwd': cwd or str(PROJECT_ROOT),
        'check': check,
        'env': env,
    }

    if timeout is not None:
        kwargs['timeout'] = timeout

    if capture:
        kwargs['capture_output'] = True
        kwargs['text'] = True
    else:
        kwargs['text'] = True

    if not interactive and not capture:
        kwargs['stdin'] = subprocess.DEVNULL

    return subprocess.run(cmd, **kwargs)  # noqa: S603


def run_compose(
    env: str,
    args: list[str],
    capture: bool = False,
    check: bool = False,
    timeout: int | None = 300,
    interactive: bool = False,
    profile: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a ``docker compose`` invocation for the given environment."""
    cmd = get_compose_cmd(env, profile=profile) + args
    return run_cmd(
        cmd,
        capture=capture,
        check=check,
        timeout=timeout,
        interactive=interactive,
    )


_PORTFOLIO_APPS = ('hub', 'generic', 'fintech', 'architect', 'leader', 'vibe')
_PORTFOLIO_PACKAGES = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')


def _default_workdir_for(service: str) -> str | None:
    """Default workdir per-service (portfolio monorepo)."""
    if service == 'server':
        return '/app/server'
    if service == 'feature':
        return '/app/tests/feature'
    if service == 'admin':
        # admin (Next.js SPA) vive en /app/admin, no bajo apps/.
        return '/app/admin'
    if service in _PORTFOLIO_APPS:
        return f'/app/apps/{service}'
    if service.startswith('pkg-'):
        pkg = service.removeprefix('pkg-')
        if pkg in _PORTFOLIO_PACKAGES:
            return f'/app/packages/{pkg}'
    return None


_PORTFOLIO_APP_SERVICES = (
    'hub',
    'generic',
    'fintech',
    'architect',
    'leader',
    'vibe',
    # admin (Next.js): el dev server corre como user app (uid 1000) sobre
    # el bind mount, igual que las apps Astro.
    'admin',
)


def _runs_as_app_user(service: str) -> bool:
    """True si el servicio debe ejecutarse como user app (uid 1000)."""
    return service in _PORTFOLIO_APP_SERVICES


def compose_exec(
    env: str,
    service: str,
    command: list[str],
    capture: bool = False,
    check: bool = False,
    timeout: int | None = 300,
    interactive: bool = False,
    workdir: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Execute a command inside a running compose service.

    Uses ``-T`` to disable pseudo-TTY allocation when capturing output, but
    leaves it enabled for interactive sessions (e.g. ``shell``, ``db-shell``).
    For apps Astro (hub, generic, ...) usa ``--user`` para no crear archivos
    root-owned en `.vite/` y `.astro/` del bind mount.

    Default workdir per-service:
        server                  -> /app/server
        feature                 -> /app/tests/feature
        admin                   -> /app/admin
        hub|generic|fintech|... -> /app/apps/<X>
        pkg-<NAME>              -> /app/packages/<NAME>
    """
    exec_args = ['exec']

    if not interactive:
        exec_args.append('-T')

    # Portfolio apps Astro: corren como root (entrypoint) pero el dev server
    # corre como `app` (uid 1000). Si invocamos exec sin --user, el comando
    # se ejecuta como root y deja archivos root-owned. Forzamos uid 1000.
    if _runs_as_app_user(service):
        uid = os.environ.get('UID', '1000')
        gid = os.environ.get('GID', '1000')
        exec_args.extend(['--user', f'{uid}:{gid}'])

    if extra_env:
        for key, value in extra_env.items():
            exec_args.extend(['-e', f'{key}={value}'])

    if workdir:
        exec_args.extend(['-w', workdir])
    else:
        default_wd = _default_workdir_for(service)
        if default_wd:
            exec_args.extend(['-w', default_wd])

    exec_args.append(service)
    exec_args.extend(command)

    return run_compose(
        env,
        exec_args,
        capture=capture,
        check=check,
        timeout=timeout,
        interactive=interactive,
    )


def is_service_running(env: str, service: str | None = None) -> bool:
    """Check whether compose services are running."""
    args = ['ps', '--status', 'running', '-q']
    if service:
        args.append(service)

    result = run_compose(env, args, capture=True)
    return bool(result.stdout.strip())


def ensure_running(env: str, auto_start: bool = True) -> bool:
    """Ensure services are running, optionally starting them."""
    if is_service_running(env):
        return True

    if not auto_start:
        err(f'Los servicios no están corriendo en ambiente {env}')
        info(f'Iniciar con: python devtools/run.py docker up --env={env}')
        return False

    warn('Los servicios no están corriendo. Iniciando...')
    result = run_compose(env, ['up', '-d'])
    if result.returncode != 0:
        err('No se pudo iniciar los servicios')
        return False

    return wait_for_healthy(env, timeout=HEALTH_CHECK_TIMEOUT)


def wait_for_healthy(env: str, timeout: int = HEALTH_CHECK_TIMEOUT) -> bool:
    """Wait until db and redis services report healthy status."""
    info(f'Esperando servicios saludables (timeout: {timeout}s)...')
    start = time.time()
    services_to_check = ['db', 'redis']

    while time.time() - start < timeout:
        all_healthy = True

        for svc in services_to_check:
            result = run_compose(
                env,
                ['ps', '--format', '{{.Health}}', svc],
                capture=True,
            )
            health = result.stdout.strip().lower()

            if 'healthy' not in health:
                all_healthy = False
                break

        if all_healthy:
            ok('Todos los servicios están saludables')
            return True

        elapsed = int(time.time() - start)
        sys.stdout.write(
            f'\r{_c(DIM, f"  Esperando... {elapsed}s/{timeout}s")}'
        )
        sys.stdout.flush()
        time.sleep(HEALTH_CHECK_INTERVAL)

    print()
    err(f'Timeout esperando servicios saludables ({timeout}s)')
    return False
