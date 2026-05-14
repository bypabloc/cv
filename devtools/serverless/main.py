"""Serverless CLI entry point.

Dispatches the parsed flags to the right command handler. Command
implementations live in domain modules (lifecycle, quality, testing,
secrets, database, observability, help) so this file stays small and
the COMMAND_REGISTRY reads as the canonical inventory of subcommands.

Sigue exactamente el patron de devtools/docker/main.py — posicional
subcommand + flag-based parameters, error handling consistente, exit
codes alineados con python.md.
"""

from __future__ import annotations

import subprocess
from typing import Any

from shared.console import _err

from serverless.database import cmd_db_branch
from serverless.database import cmd_db_migrate
from serverless.database import cmd_db_rollback
from serverless.database import cmd_db_seed
from serverless.database import cmd_db_shell
from serverless.database import cmd_db_tables
from serverless.help import cmd_help
from serverless.lifecycle import cmd_build
from serverless.lifecycle import cmd_clean
from serverless.lifecycle import cmd_delete
from serverless.lifecycle import cmd_deploy
from serverless.lifecycle import cmd_init
from serverless.lifecycle import cmd_invoke
from serverless.lifecycle import cmd_logs
from serverless.lifecycle import cmd_smoke
from serverless.lifecycle import cmd_start_api
from serverless.lifecycle import cmd_tail
from serverless.lifecycle import cmd_validate
from serverless.observability import cmd_alarms
from serverless.observability import cmd_metrics
from serverless.quality import cmd_format
from serverless.quality import cmd_lint
from serverless.quality import cmd_lint_fix
from serverless.quality import cmd_typecheck
from serverless.secrets import cmd_request_ses_prod
from serverless.secrets import cmd_rotate_secret
from serverless.secrets import cmd_setup_ssm
from serverless.secrets import cmd_verify_ses_dns
from serverless.testing import cmd_test
from serverless.testing import cmd_test_coverage
from serverless.testing import cmd_test_integration
from serverless.testing import cmd_test_unit


COMMAND_REGISTRY: dict[str, Any] = {
    # Lifecycle
    'init': cmd_init,
    'validate': cmd_validate,
    'build': cmd_build,
    'deploy': cmd_deploy,
    'delete': cmd_delete,
    # Local development
    'invoke': cmd_invoke,
    'start-api': cmd_start_api,
    'logs': cmd_logs,
    'tail': cmd_tail,
    # Quality
    'lint': cmd_lint,
    'lint-fix': cmd_lint_fix,
    'format': cmd_format,
    'typecheck': cmd_typecheck,
    # Tests
    'test': cmd_test,
    'test-unit': cmd_test_unit,
    'test-integration': cmd_test_integration,
    'test-coverage': cmd_test_coverage,
    # Secrets / DNS
    'setup-ssm': cmd_setup_ssm,
    'rotate-secret': cmd_rotate_secret,
    'verify-ses-dns': cmd_verify_ses_dns,
    'request-ses-prod': cmd_request_ses_prod,
    # Database (Neon)
    'db-shell': cmd_db_shell,
    'db-migrate': cmd_db_migrate,
    'db-rollback': cmd_db_rollback,
    'db-seed': cmd_db_seed,
    'db-branch': cmd_db_branch,
    'db-tables': cmd_db_tables,
    # Observability
    'metrics': cmd_metrics,
    'alarms': cmd_alarms,
    # Maintenance
    'smoke': cmd_smoke,
    'clean': cmd_clean,
    'help': cmd_help,
}


def main(flags: dict[str, Any]) -> int:
    """Entry point invoked by devtools/run.py.

    The `flags` dict comes pre-validated by `serverless.flags.flag()`
    (invoked by `devtools/run.py` before main()). At this point it
    contains a normalized `command` key, defaults applied, and stage /
    function choices validated.

    Failures bubble up as non-zero exit codes:
      - 1: error de ejecucion
      - 130: KeyboardInterrupt (Ctrl+C)
    """
    command = flags.get('command', 'help')
    handler = COMMAND_REGISTRY.get(command)

    if handler is None:
        _err(f'Comando desconocido: {command}')
        cmd_help(flags)
        return 1

    try:
        return handler(flags)
    except subprocess.TimeoutExpired:
        _err(f'Timeout ejecutando: {command}')
        return 1
    except KeyboardInterrupt:
        print()
        _err('Operacion interrumpida por el usuario')
        return 130
    except (subprocess.SubprocessError, OSError, ValueError, TypeError) as e:
        _err(f'Error ejecutando {command}: {e}')
        return 1
