"""Cache management commands: clear and show status of Python caches.

Operates on local ``__pycache__``/.ruff_cache/.pytest_cache and on the
matching directories inside the running ``server`` container. Both halves
matter: bytecode lives outside the container while pytest cache lives
inside.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
from typing import Any

from docker._helpers import dir_size as _dir_size
from docker._helpers import format_size as _format_size
from shared.compose import compose_exec
from shared.compose import is_service_running
from shared.console import BOLD
from shared.console import DIM
from shared.console import _c
from shared.console import _header
from shared.console import _info
from shared.console import _ok
from shared.console import _step
from shared.paths import PROJECT_ROOT


def _clear_pycache_local() -> None:
    """Remove __pycache__ directories from the local project tree."""
    removed = 0
    for root, dirs, _files in os.walk(str(PROJECT_ROOT)):
        for d in dirs:
            if d == '__pycache__':
                cache_path = os.path.join(root, d)
                try:
                    shutil.rmtree(cache_path)
                    removed += 1
                except OSError as exc:
                    print(
                        f'Advertencia: no se pudo eliminar {cache_path}: {exc}'
                    )
    if removed > 0:
        _info(f'Eliminados {removed} directorios __pycache__ locales')


def _clear_pycache_container(env: str) -> int:
    """Remove __pycache__ directories inside the server container."""
    result = compose_exec(
        env,
        'server',
        [
            'find',
            '/app',
            '-type',
            'd',
            '-name',
            '__pycache__',
            '-exec',
            'rm',
            '-rf',
            '{}',
            '+',
        ],
    )
    return result.returncode


def cmd_cache_clear_all(flags: dict[str, Any]) -> int:
    """Clear all Python caches locally and in containers."""
    env = flags['env']

    _header(f'cache clear [{env}]')

    _step('Limpiando caches locales...')
    _clear_pycache_local()

    if is_service_running(env, 'server'):
        _step('Limpiando caches en container...')
        _clear_pycache_container(env)
    else:
        _info('Server no esta corriendo, omitiendo limpieza en container')

    for cache in (
        PROJECT_ROOT / '.ruff_cache',
        PROJECT_ROOT / 'server' / '.ruff_cache',
        PROJECT_ROOT / 'server' / '.pytest_cache',
    ):
        if cache.exists():
            shutil.rmtree(str(cache), ignore_errors=True)
            rel = cache.relative_to(PROJECT_ROOT)
            _info(f'Eliminado {rel}')

    _ok('Caches limpiados')
    return 0


def _count_pycache_dirs() -> tuple[int, int]:
    """Count __pycache__ dirs and their total size."""
    count = 0
    total_size = 0
    for root, dirs, _files in os.walk(str(PROJECT_ROOT)):
        for d in dirs:
            if d == '__pycache__':
                count += 1
                total_size += _dir_size(os.path.join(root, d))
    return count, total_size


def _print_cache_dir(label: str, path: Path) -> None:
    """Print a cache directory status line."""
    if path.exists():
        size = _dir_size(str(path))
        print(f'    {label:<22s}{_format_size(size)}')
    else:
        print(f'    {label:<22s}{_c(DIM, "no existe")}')


def _print_container_caches(env: str) -> None:
    """Print container cache info."""
    if not is_service_running(env, 'server'):
        print(
            f'  {_c(BOLD, "Container caches:")} {_c(DIM, "server no corriendo")}'
        )
        return

    print(f'  {_c(BOLD, "Container caches:")}')
    result = compose_exec(
        env,
        'server',
        ['find', '/app', '-type', 'd', '-name', '__pycache__'],
        capture=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        container_count = len(result.stdout.strip().split('\n'))
        print(f'    __pycache__ dirs:     {container_count}')
    else:
        print('    __pycache__ dirs:     0')


def cmd_cache_status(flags: dict[str, Any]) -> int:
    """Show cache status information.

    With ``--output=json`` emits structured data: pycache counts/sizes and
    which cache dirs exist. Easier to consume from agents/CI than parsing
    the human table.
    """
    env = flags['env']
    output = flags.get('output', 'text')

    pycache_count, pycache_total_size = _count_pycache_dirs()

    if output == 'json':
        import json

        def _entry(path: Path) -> dict[str, Any]:
            if path.exists():
                return {'exists': True, 'size_bytes': _dir_size(str(path))}
            return {'exists': False, 'size_bytes': 0}

        payload = {
            'local': {
                'pycache_dirs': pycache_count,
                'pycache_size_bytes': pycache_total_size,
                'ruff_cache_root': _entry(PROJECT_ROOT / '.ruff_cache'),
                'ruff_cache_server': _entry(
                    PROJECT_ROOT / 'server' / '.ruff_cache'
                ),
                'pytest_cache_server': _entry(
                    PROJECT_ROOT / 'server' / '.pytest_cache'
                ),
            },
            'container': {
                'server_running': is_service_running(env, 'server'),
            },
        }
        print(json.dumps(payload, indent=2))
        return 0

    _header(f'cache status [{env}]')
    print()
    print(f'  {_c(BOLD, "Local caches:")}')
    print(f'    __pycache__ dirs:     {pycache_count}')
    print(f'    __pycache__ size:     {_format_size(pycache_total_size)}')

    _print_cache_dir('.ruff_cache:', PROJECT_ROOT / '.ruff_cache')
    _print_cache_dir(
        'server/.ruff_cache:', PROJECT_ROOT / 'server' / '.ruff_cache'
    )
    _print_cache_dir(
        'server/.pytest_cache:',
        PROJECT_ROOT / 'server' / '.pytest_cache',
    )

    print()
    _print_container_caches(env)

    print()
    return 0
