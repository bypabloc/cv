"""Help command for serverless CLI.

Renders a colourised inventory of subcommands grouped by domain.
"""

from typing import Any

from shared.console import BOLD
from shared.console import CYAN
from shared.console import DIM
from shared.console import GREEN
from shared.console import NC
from shared.console import RED
from shared.console import YELLOW
from shared.console import _c

from serverless.flags import _COMMAND_FLAGS
from serverless.flags import _COMMAND_SUMMARIES
from serverless.flags import DESTRUCTIVE_COMMANDS
from serverless.flags import VALID_COMMANDS
from serverless.flags import VALID_FUNCTIONS
from serverless.flags import VALID_STAGES


# Mapeo comando -> grupo para render organizado
_GROUPS: dict[str, list[str]] = {
    'Lifecycle': ['init', 'validate', 'build', 'deploy', 'delete'],
    'Local development': ['invoke', 'start-api', 'logs', 'tail'],
    'Quality': ['lint', 'lint-fix', 'format', 'typecheck'],
    'Tests': ['test', 'test-unit', 'test-integration', 'test-coverage'],
    'Secrets / DNS': [
        'setup-ssm',
        'rotate-secret',
        'verify-ses-dns',
        'request-ses-prod',
    ],
    'Database (Neon PG)': [
        'db-shell',
        'db-migrate',
        'db-rollback',
        'db-current',
        'db-show-migrations',
        'db-seed',
        'db-branch',
        'db-tables',
    ],
    'Observability': ['metrics', 'alarms'],
    'Rate-limit (DynamoDB self-managed, alternativa $0 a WAF)': ['rate-limit'],
    'Maintenance': ['smoke', 'clean', 'help'],
}


def cmd_help(flags: dict[str, Any]) -> int:
    """Imprime ayuda colorizada del CLI serverless."""
    print()
    print(_c(BOLD, 'serverless') + ' ' + _c(DIM, '— backend SAM del portfolio'))
    print(
        _c(
            DIM,
            '  Lambdas Python 3.13 (arm64) + API Gateway + DynamoDB + SES + Neon PG',
        )
    )
    print()
    print(_c(YELLOW, 'Uso:'))
    print(
        f'  python devtools/run.py serverless '
        f'{_c(CYAN, "<command>")} '
        f'{_c(DIM, "[--stage=local] [flags...]")}'
    )
    print()
    print(_c(YELLOW, 'Stages:'))
    for stage in VALID_STAGES:
        print(f'  {_c(GREEN, stage):<20}')
    print()
    print(_c(YELLOW, 'Functions:'))
    for fn in VALID_FUNCTIONS:
        print(f'  {_c(CYAN, fn):<25}')
    print()

    for group_name, commands in _GROUPS.items():
        print(_c(BOLD + YELLOW, group_name))
        for cmd in commands:
            if cmd not in VALID_COMMANDS:
                continue
            summary = _COMMAND_SUMMARIES.get(cmd, '')
            flag_list = _COMMAND_FLAGS.get(cmd, [])
            destructive_marker = (
                _c(RED, ' [destructivo]') if cmd in DESTRUCTIVE_COMMANDS else ''
            )
            flag_hint = (
                _c(DIM, f'  ({", ".join("--" + f for f in flag_list)})')
                if flag_list
                else ''
            )
            print(
                f'  {_c(CYAN, cmd):<35} {summary}'
                f'{destructive_marker}{flag_hint}',
            )
        print()

    print(_c(DIM, '  Documentacion: serverless/README.md'))
    print(
        _c(DIM, '  Conocimiento: .claude/docs/aws-lambda/, .claude/docs/neon/')
    )
    print()
    return 0
