"""Serverless CLI entry point.

Dispatches the parsed flags to the right command handler. Command
implementations live in domain modules (lifecycle, quality,
lambda_controller, secrets, observability, help) so this file stays
small and the COMMAND_REGISTRY reads as the canonical inventory of
subcommands. Las operaciones de base de datos se hacen invocando la
Lambda `db` con `run --lambda=db --event=events/<X>.json`.

Sigue exactamente el patron de devtools/docker/main.py — posicional
subcommand + flag-based parameters, error handling consistente, exit
codes alineados con python.md.
"""

from __future__ import annotations

import subprocess
from typing import Any

from serverless.change_detector import cmd_detect_changes
from serverless.dep_validator import cmd_lint_deps
from serverless.email_seed import cmd_seed_email_config
from serverless.help import cmd_help
from serverless.infra_provision import cmd_list_resources
from serverless.infra_provision import cmd_provision_infra
from serverless.lambda_controller import cmd_deploy_lambda
from serverless.lambda_controller import cmd_destroy
from serverless.lambda_controller import cmd_run
from serverless.lambda_controller import cmd_status
from serverless.lambda_controller import cmd_tests
from serverless.lifecycle import cmd_clean
from serverless.lifecycle import cmd_init
from serverless.observability import cmd_alarms
from serverless.observability import cmd_metrics
from serverless.quality import cmd_format
from serverless.quality import cmd_lint
from serverless.quality import cmd_lint_fix
from serverless.quality import cmd_typecheck
from serverless.rate_limit_cmds import cmd_rate_limit
from serverless.secrets import cmd_request_ses_prod
from serverless.secrets import cmd_rotate_secret
from serverless.secrets import cmd_secrets_status
from serverless.secrets import cmd_setup_ssm
from serverless.secrets import cmd_sync_secrets
from serverless.secrets import cmd_validate_catalog
from serverless.secrets import cmd_verify_ses_dns
from shared.console import _err


COMMAND_REGISTRY: dict[str, Any] = {
    # Setup / Maintenance
    'init': cmd_init,
    'clean': cmd_clean,
    # Quality (Ruff + mypy sobre serverless/lambda/shared/ y serverless/lambda/services/)
    'lint': cmd_lint,
    'lint-fix': cmd_lint_fix,
    'lint-deps': cmd_lint_deps,
    'detect-changes': cmd_detect_changes,
    'format': cmd_format,
    'typecheck': cmd_typecheck,
    # Tests: unico comando, --type=unit|integration|coverage + target
    'tests': cmd_tests,
    # lambda-controller: ciclo de vida de cada Lambda. devtools provisiona
    # cada Lambda con AWS CLI directo (sin SAM): deploy traduce el
    # manifiesto a llamadas AWS, run lo ejecuta con RIE / modo directo.
    'run': cmd_run,
    'deploy': cmd_deploy_lambda,
    'destroy': cmd_destroy,
    'status': cmd_status,
    # Infra: recursos compartidos provisionados con AWS CLI directo.
    'provision-infra': cmd_provision_infra,
    'list-resources': cmd_list_resources,
    # Email: seed de templates (S3) + filas de config (DynamoDB).
    'seed-email-config': cmd_seed_email_config,
    # Secrets / DNS
    'setup-ssm': cmd_setup_ssm,
    'rotate-secret': cmd_rotate_secret,
    'sync-secrets': cmd_sync_secrets,
    'secrets-status': cmd_secrets_status,
    'validate-catalog': cmd_validate_catalog,
    'verify-ses-dns': cmd_verify_ses_dns,
    'request-ses-prod': cmd_request_ses_prod,
    # Observability
    'metrics': cmd_metrics,
    'alarms': cmd_alarms,
    # Rate-limit management (alternativa $0 a AWS WAF)
    'rate-limit': cmd_rate_limit,
    # Help
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
