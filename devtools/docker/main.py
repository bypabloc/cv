"""Docker CLI entry point.

Dispatches the parsed flags to the right command handler. Command
implementations live in domain modules (lifecycle, quality, database,
setup, cache, help) so this file stays small and the
``COMMAND_REGISTRY`` reads as the canonical inventory of subcommands.

The ``test`` subcommand was removed in Fase 3 of the CLI refactor;
``test_runner`` is now the single source of truth for running tests. The
shim here returns an actionable migration message so existing scripts and
docs that still reach for ``docker test`` get a clear pointer.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from docker.cache import cmd_cache_clear_all
from docker.cache import cmd_cache_status
from docker.database import cmd_db_count
from docker.database import cmd_db_describe
from docker.database import cmd_db_reset
from docker.database import cmd_db_seed
from docker.database import cmd_db_shell
from docker.database import cmd_db_tables
from docker.help import cmd_help
from docker.lifecycle import cmd_build
from docker.lifecycle import cmd_down
from docker.lifecycle import cmd_exec
from docker.lifecycle import cmd_logs
from docker.lifecycle import cmd_ps
from docker.lifecycle import cmd_restart
from docker.lifecycle import cmd_shell
from docker.lifecycle import cmd_up
from docker.lifecycle_recovery import cmd_rebuild
from docker.lifecycle_recovery import cmd_refresh
from docker.quality import cmd_format
from docker.quality import cmd_lint
from docker.quality import cmd_lint_fix
from docker.setup import cmd_clean
from docker.setup import cmd_setup
from shared.console import CYAN
from shared.console import NC
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


def cmd_test_removed(flags: dict[str, Any]) -> int:
    """Migration shim: ``docker test`` was removed in favour of ``test_runner``."""
    _err("'docker test' fue removido del CLI.")
    print()
    print(
        f'{_c(YELLOW, "Migración:")} usa '
        f'{_c(CYAN, "python devtools/run.py test_runner")} '
        'para ejecutar tests.'
    )
    print()
    print('Equivalencias:')
    print(
        '  docker test --type=unit            ->  '
        'test_runner --module=pkg-content --type=unit'
    )
    print(
        '  docker test --module=generic ...   ->  '
        'test_runner --module=generic ...'
    )
    print(
        '  docker test --module=feature ...   ->  '
        'test_runner --module=feature --type=feature'
    )
    print()
    print('Documentación: python devtools/run.py test_runner --help')
    return 1


COMMAND_REGISTRY: dict[str, Any] = {
    # Lifecycle
    'up': cmd_up,
    'down': cmd_down,
    'build': cmd_build,
    'rebuild': cmd_rebuild,
    'logs': cmd_logs,
    'shell': cmd_shell,
    'exec': cmd_exec,
    'ps': cmd_ps,
    'restart': cmd_restart,
    'refresh': cmd_refresh,
    # Quality
    'lint': cmd_lint,
    'lint-fix': cmd_lint_fix,
    'format': cmd_format,
    # 'test' eliminado intencionalmente — usar `test_runner` (Fase 3)
    'test': cmd_test_removed,
    # Database
    'db-shell': cmd_db_shell,
    'db-tables': cmd_db_tables,
    'db-describe': cmd_db_describe,
    'db-count': cmd_db_count,
    'db-seed': cmd_db_seed,
    'db-reset': cmd_db_reset,
    # Setup
    'setup': cmd_setup,
    'clean': cmd_clean,
    'help': cmd_help,
    # Cache
    'cache-clear-all': cmd_cache_clear_all,
    'cache-status': cmd_cache_status,
}


def main(flags: dict[str, Any]) -> int:
    """Entry point invoked by devtools/run.py.

    The ``flags`` dict is pre-validated by ``docker/flags.py`` and contains
    a ``command`` key. Failures from handlers bubble up as non-zero exit
    codes; KeyboardInterrupt returns 130.
    """
    command = flags.get('command', 'help')
    handler = COMMAND_REGISTRY.get(command)

    if handler is None:
        _err(f'Comando desconocido: {command}')
        cmd_help(flags)
        return 1

    if command != 'help' and not shutil.which('docker'):
        _err('Docker no esta disponible')
        print(
            f'{YELLOW}  Docker Desktop debe estar corriendo '
            f'con la integración WSL2 activada.{NC}',
        )
        print(f'{CYAN}  1. Abrir Docker Desktop en Windows{NC}')
        print(
            f'{CYAN}  2. Settings > Resources > WSL Integration '
            f'> activar tu distro{NC}',
        )
        print(f'{CYAN}  3. Reintentar el comando{NC}')
        return 1

    try:
        return handler(flags)
    except subprocess.TimeoutExpired:
        _err(f'Timeout ejecutando comando: {command}')
        return 1
    except KeyboardInterrupt:
        print()
        _err('Operación interrumpida por el usuario')
        return 130
    except (
        subprocess.SubprocessError,
        OSError,
        ValueError,
        TypeError,
    ) as e:
        _err(f'Error ejecutando {command}: {e}')
        return 1
