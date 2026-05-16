"""Internal helpers for the docker CLI.

Module-private functions that several command files share but that are
not generic enough for ``shared/`` (they encode docker compose / nginx
specifics of this project: db credentials, profile resolution, byte
formatting). URL discovery lives in ``docker/urls.py``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

from shared.console import BOLD
from shared.console import RED
from shared.console import YELLOW
from shared.console import _c
from shared.console import _info
from shared.console import _warn
from shared.paths import DOCKER_DIR
from shared.project_config import PROJECT_NAME_SNAKE


SERVICES = [
    'nginx',
    # Portfolio apps Astro
    'generic',
    'hub',
    'fintech',
    'architect',
    'leader',
    'vibe',
    # Feature tests shared (Playwright)
    'feature',
]

DB_DEFAULTS = {
    'user': PROJECT_NAME_SNAKE,
    'name': PROJECT_NAME_SNAKE,
}


def get_db_credentials(env: str) -> dict[str, str]:
    """Read Postgres credentials from the env file, falling back to defaults.

    Los campos de DB no sensibles viven en la categoria ``server`` desde el
    refactor de env files por sensibilidad (client / server / dev-cli).
    """
    env_file = DOCKER_DIR / 'env' / 'server' / f'.{env}'
    creds = dict(DB_DEFAULTS)

    if not env_file.exists():
        return creds

    try:
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                if key == 'POSTGRES_USER':
                    creds['user'] = value
                elif key == 'POSTGRES_DB':
                    creds['db'] = value
    except OSError as exc:
        print(f'Advertencia: no se pudo leer env file: {exc}')

    return creds


def confirm_destructive(message: str) -> bool:
    """Ask user to confirm a destructive operation.

    Returns False on EOF/Ctrl-C (non-interactive contexts) so the caller
    short-circuits without doing damage.
    """
    print()
    _warn(f'{_c(RED, "OPERACIÓN DESTRUCTIVA")}')
    print(f'  {message}')
    print()

    try:
        answer = input(
            f'{_c(YELLOW, "Confirmar?")} Escribe {_c(BOLD, "yes")} para continuar: '
        )
    except EOFError, KeyboardInterrupt:
        print()
        _info('Operación cancelada')
        return False

    if answer.strip().lower() != 'yes':
        _info('Operación cancelada')
        return False

    return True


def resolve_profile(flags: dict[str, Any]) -> str | None:
    """Resolve compose profile from flags (--profile or --service auto-resolve).

    1. Explicit ``--profile=<name>`` wins.
    2. Auto-resolved from ``--service=<name>`` via PROFILE_SERVICES.
    3. None (default profile only).
    """
    explicit = flags.get('profile')
    if explicit:
        return str(explicit)

    service = flags.get('service')
    if service:
        from docker.flags import PROFILE_SERVICES

        return PROFILE_SERVICES.get(str(service))

    return None


def print_captured_output(
    result: subprocess.CompletedProcess[str],
) -> None:
    """Print captured stdout/stderr from a subprocess result."""
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)


def dir_size(path: str) -> int:
    """Return total size in bytes of a directory tree (best-effort)."""
    import contextlib

    total = 0
    with contextlib.suppress(OSError):
        for root, _, files in os.walk(path):
            for name in files:
                fp = os.path.join(root, name)
                with contextlib.suppress(OSError):
                    total += os.path.getsize(fp)
    return total


def format_size(size_bytes: int) -> str:
    """Format a byte count as a human-readable string (B, KB, MB, GB)."""
    if size_bytes < 1024:
        return f'{size_bytes} B'
    if size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.1f} KB'
    if size_bytes < 1024 * 1024 * 1024:
        return f'{size_bytes / (1024 * 1024):.1f} MB'
    return f'{size_bytes / (1024 * 1024 * 1024):.1f} GB'


# Re-export URL helpers from docker.urls so existing call sites that imported
# them from _helpers keep working.
from docker.urls import (  # noqa: E402  (intentional late import to avoid cycle)
    parse_compose_ports,
)
from docker.urls import (  # noqa: E402  (intentional late import to avoid cycle)
    parse_nginx_subdomains,
)
from docker.urls import (  # noqa: E402  (intentional late import to avoid cycle)
    print_service_urls,
)
