"""Flag validation and configuration for serverless CLI script.

Validates and normalizes flags for the AWS SAM backend module. Like
``docker``, this module takes a positional subcommand (NOT `--command=`)
plus flag-based parameters. See ``.claude/rules/devtools.md`` for the
posicional-vs-flag policy.
"""

import sys
from typing import Any

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


# Stages soportados por el backend SAM. Se mapean a samconfig.toml
# environments. ``local`` no es un stage AWS real — apunta a sam local
# invoke + sam local start-api + moto mocks.
VALID_STAGES = ['local', 'dev', 'stage', 'prod']

STAGE_DESCRIPTIONS = {
    'local': 'sam local invoke / start-api con moto mocks (sin AWS)',
    'dev': 'Stack desplegado en us-east-1 (cuenta dev / sandbox)',
    'stage': 'Stack de pre-produccion en us-east-1 (replica prod)',
    'prod': 'Stack desplegado en us-east-1 (cuenta productiva)',
}

# Funciones Lambda del modulo. Coinciden con el LogicalId del template.yaml.
VALID_FUNCTIONS = [
    'contact-form',
    'tracking-pixel',
    'stream-processor',  # DynamoDB Streams -> Neon PG
]

# Tablas DynamoDB administradas por el modulo. Usadas por subcomandos
# ``db-*`` para scope explicito.
VALID_TABLES = ['contacts', 'tracking']

VALID_COMMANDS = [
    # Lifecycle
    'init',  # uv sync + first-time setup (alias de pyproject)
    'validate',  # sam validate template.yaml
    'build',  # sam build --use-container (cross-platform arm64)
    'deploy',  # sam deploy (guided si stage no existe)
    'delete',  # sam delete (destructivo, requiere --confirm)
    # Local development (no AWS)
    'invoke',  # sam local invoke <function> --event events/X.json
    'start-api',  # sam local start-api --port 3000
    'logs',  # sam logs -n <function> --tail
    # Quality
    'lint',  # Ruff check sobre serverless/src/
    'lint-fix',  # Ruff check --fix
    'format',  # Ruff format
    'typecheck',  # mypy (si configurado) sobre src/
    # Tests
    'test',  # pytest tests/unit + integration
    'test-unit',  # pytest tests/unit -m unit
    'test-integration',  # pytest tests/integration -m integration
    'test-coverage',  # pytest --cov=src
    # lambda-controller dinamico (lambdas con lambda.yaml, fuera del SAM
    # del portfolio). Requieren --path=<dir>.
    'sam-generate',  # lambda.yaml -> template.yaml (SAM efimero)
    'run-local',  # sam local invoke del lambda-controller
    'invoke-remote',  # aws lambda invoke contra un stage deployado
    'deploy-infra',  # deploya el stack de infra compartida (5-stacks)
    # Secrets / Setup AWS resources fuera del template
    'setup-ssm',  # Crear SSM Parameters (turnstile-secret, neon-url)
    'rotate-secret',  # Rotar valor de un SSM Parameter
    'verify-ses-dns',  # dig DKIM/SPF/DMARC contra Cloudflare
    'request-ses-prod',  # Imprime plantilla del ticket SES production access
    # Database (Neon PostgreSQL) — migraciones via la Lambda `db` (Alembic)
    'db-shell',  # psql interactivo contra Neon (lee connection string de SSM)
    'db-migrate',  # alembic upgrade via Lambda db (aplica migraciones)
    'db-rollback',  # alembic downgrade via Lambda db (DESTRUCTIVO)
    'db-current',  # alembic current via Lambda db (revision aplicada)
    'db-show-migrations',  # alembic history via Lambda db
    'db-seed',  # Carga data de prueba en Neon
    'db-branch',  # Crea / lista / borra branches de Neon (neon CLI)
    'db-tables',  # Lista tablas + row counts
    # Observability
    'tail',  # sam logs -n <function> --tail (alias verbose de `logs --follow`)
    'metrics',  # CloudWatch metrics summary del stack
    'alarms',  # Lista alarmas y su estado
    # Rate-limit management (alternativa $0 a AWS WAF)
    'rate-limit',  # Dispatcher: list|show|set|allow|block|unblock|stats|clear-buckets
    # Smoke / Maintenance
    'smoke',  # scripts/smoke_test.sh (curl contra endpoint real)
    'clean',  # rm -rf .aws-sam/ + __pycache__ + .pytest_cache
    'help',  # Ayuda colorizada
]

# Flags aceptados (validados en validate_allowed_flags). El handler usa
# solo los relevantes a su subcomando.
ALLOWED_FLAGS = [
    # Stage
    'stage',
    # lambda-controller dinamico
    'path',  # --path=<dir> del lambda-controller (dir con lambda.yaml)
    'module',  # alias de --path
    # Lifecycle
    'guided',  # sam deploy --guided
    'confirm',  # required para 'delete' (no destructivo accidental)
    'no_cache',  # sam build --no-cache (rebuild from scratch)
    'parameter_overrides',  # sam deploy --parameter-overrides
    # Local invoke
    'function',  # --function=contact-form
    'event',  # --event=events/contact_form_valid.json
    'port',  # sam local start-api --port=3000
    'debug',  # sam local invoke --debug
    # Logs
    'tail',  # --tail (continuous follow)
    'follow',  # alias de tail
    'since',  # --since=10m (timeframe de logs)
    'filter',  # --filter='ERROR' (CloudWatch filter pattern)
    # Quality / Tests
    'module_path',  # Subset del codigo (ej. src/contact_form/)
    'files',  # Subset de archivos especificos
    'verbose',
    'v',  # alias de verbose
    'quiet',
    'output_format',
    # Test
    'marker',  # pytest -m <marker>
    'coverage_threshold',  # default 80
    # Secrets
    'name',  # --name=/portfolio/turnstile-secret
    'value',  # --value=... (preferir leer de stdin para no leak shell history)
    'key_id',  # --key-id=alias/portfolio-lambdas
    # Database
    'table',  # --table=contacts
    'branch',  # --branch=dev-feature-X (Neon branching)
    'parent',  # --parent=main (parent branch)
    'target',  # --target=head|-1|base|<revision> (Alembic, via Lambda db)
    'dry_run',  # No aplica, solo imprime acciones
    # Rate-limit management
    'endpoint',  # --endpoint=/contact (rate-limit set)
    'country',  # --country=CL (ISO 3166-1 alpha-2)
    'limit',  # --limit=3 (max requests per window)
    'window',  # --window=300 (seconds)
    'action',  # --action=throttle|block|allow
    'ip',  # --ip=X.X.X.X
    'ttl',  # --ttl=86400 (seconds, blacklist temporal)
    'reason',  # --reason="why" (audit string)
    # Cross-cutting
    'output',  # json|text
    'profile',  # --profile=tfs-dev (perfil AWS CLI)
    # Internal
    'command',
    'subcommands',
    'help',
]


# Comandos destructivos. Cada uno requiere --confirm o --dry-run primero.
DESTRUCTIVE_COMMANDS = frozenset(
    {
        'delete',
        'clean',
        'db-rollback',
        'rotate-secret',
    }
)


# Comandos del modo lambda-controller dinamico: requieren --path=<dir>.
PATH_REQUIRED_COMMANDS = frozenset(
    {
        'sam-generate',
        'run-local',
        'invoke-remote',
    }
)


# Comandos que soportan --output=json para integracion CI/scripts.
JSON_OUTPUT_COMMANDS = frozenset(
    {
        'metrics',
        'alarms',
        'db-tables',
        'logs',
    }
)


# Resumenes 1-line por comando (usados por describe() y help).
_COMMAND_SUMMARIES: dict[str, str] = {
    'init': 'Setup inicial (uv sync + verifica AWS CLI + SAM)',
    'validate': 'sam validate template.yaml',
    'build': 'sam build --use-container (arm64 cross-platform)',
    'deploy': 'sam deploy a stage (--guided si primera vez)',
    'delete': 'sam delete del stack (DESTRUCTIVO)',
    'invoke': 'sam local invoke <function> --event events/X.json',
    'start-api': 'sam local start-api (server HTTP local)',
    'logs': 'sam logs -n <function> (real-time o ventana)',
    'lint': 'Ruff check sobre src/',
    'lint-fix': 'Ruff check --fix',
    'format': 'Ruff format',
    'typecheck': 'mypy strict sobre src/',
    'test': 'pytest unit + integration',
    'test-unit': 'pytest tests/unit (--path para lambda-controller)',
    'test-integration': 'pytest tests/integration (--path lambda-controller)',
    'test-coverage': 'pytest --cov=src (threshold 80% per-file)',
    'sam-generate': 'Genera template.yaml SAM desde lambda.yaml (--path)',
    'run-local': 'sam local invoke de un lambda-controller (--path)',
    'invoke-remote': 'aws lambda invoke contra un stage deployado (--path)',
    'setup-ssm': 'Crear SSM Parameters con KMS (turnstile, neon-url)',
    'rotate-secret': 'Rotar valor de un SSM Parameter (DESTRUCTIVO)',
    'verify-ses-dns': 'dig CNAMEs DKIM + TXT SPF/DMARC vs Cloudflare',
    'request-ses-prod': 'Plantilla del ticket de production access SES',
    'db-shell': 'psql contra Neon (lee URL de SSM)',
    'db-migrate': 'alembic upgrade via Lambda db (aplica migraciones)',
    'db-rollback': 'alembic downgrade via Lambda db (DESTRUCTIVO)',
    'db-current': 'Revision Alembic aplicada en la DB',
    'db-show-migrations': 'Historial de migraciones Alembic',
    'db-seed': 'Cargar data de prueba',
    'db-branch': 'CRUD de branches Neon (create/list/delete)',
    'db-tables': 'Listar tablas Neon + row counts',
    'tail': 'sam logs --tail (alias verbose de logs --follow)',
    'metrics': 'Resumen CloudWatch metrics del stack',
    'alarms': 'Lista alarmas + estado',
    'rate-limit': 'Gestion de reglas rate-limit (list|set|allow|block|stats|...)',
    'smoke': 'curl contra endpoint deployed (smoke test)',
    'clean': 'Eliminar .aws-sam/ + caches Python',
    'help': 'Ayuda colorizada',
}


# Flags relevantes por comando (informativo para describe() y completion).
_COMMAND_FLAGS: dict[str, list[str]] = {
    'init': [],
    'validate': [],
    'build': ['no_cache', 'function'],
    'deploy': ['stage', 'guided', 'parameter_overrides'],
    'delete': ['stage', 'confirm', 'dry_run'],
    'invoke': ['function', 'event', 'debug'],
    'start-api': ['port', 'debug'],
    'logs': ['function', 'tail', 'follow', 'since', 'filter', 'output'],
    'lint': ['module_path', 'files', 'output_format'],
    'lint-fix': ['module_path', 'files'],
    'format': ['module_path', 'files'],
    'typecheck': ['module_path'],
    'test': ['verbose', 'coverage_threshold'],
    'test-unit': ['verbose', 'marker', 'files', 'path', 'module'],
    'test-integration': ['verbose', 'marker', 'path', 'module'],
    'test-coverage': ['coverage_threshold'],
    'sam-generate': ['path', 'module', 'stage'],
    'run-local': ['path', 'module', 'stage', 'event', 'debug'],
    'invoke-remote': ['path', 'module', 'stage', 'event'],
    'setup-ssm': ['stage', 'name', 'value', 'key_id'],
    'rotate-secret': ['stage', 'name', 'value', 'confirm'],
    'verify-ses-dns': [],
    'request-ses-prod': [],
    'db-shell': ['stage', 'branch'],
    'db-migrate': ['stage', 'target', 'dry_run'],
    'db-rollback': ['stage', 'target', 'confirm', 'dry_run'],
    'db-current': ['stage'],
    'db-show-migrations': ['stage'],
    'db-seed': ['stage', 'dry_run'],
    'db-branch': ['parent', 'branch', 'subcommands'],
    'db-tables': ['stage', 'output'],
    'tail': ['function', 'since', 'filter'],
    'metrics': ['stage', 'since', 'output'],
    'alarms': ['stage', 'output'],
    'rate-limit': [
        'subcommands',
        'endpoint',
        'country',
        'limit',
        'window',
        'action',
        'ip',
        'ttl',
        'reason',
        'output',
        'since',
        'confirm',
        'dry_run',
        'name',
    ],
    'smoke': ['stage'],
    'clean': ['dry_run'],
    'help': [],
}


# Defaults aplicados por set_default_values cuando un flag no se provee.
_DEFAULTS: dict[str, Any] = {
    'stage': 'local',
    'guided': False,
    'confirm': False,
    'no_cache': False,
    'port': 3000,
    'debug': False,
    'tail': False,
    'follow': False,
    'since': '10m',
    'verbose': False,
    'quiet': False,
    'output_format': 'text',
    'coverage_threshold': 80,
    'dry_run': False,
    'output': 'text',
    'parent': 'main',
}


def _extract_positionals(flags_dict: dict[str, Any]) -> None:
    """Extract positional args from sys.argv into flags_dict['subcommands'].

    `flags_to_dict` solo parsea `--key=value`; los positionals (e.g.
    `serverless build`, `serverless db-branch create --branch=X`) se
    pierden. Este helper los reconstruye desde `sys.argv[2:]` (saltando
    el nombre del script) tomando todo lo que NO arranque con `--`.

    Mismo patron que `devtools/docker/flags.py::_extract_command`.
    """
    import sys as _sys

    raw_args = _sys.argv[2:]
    positionals: list[str] = []
    for arg in raw_args:
        if arg == '--':
            break
        if not arg.startswith('--'):
            positionals.append(arg)

    if positionals:
        # Si `flags_dict['subcommands']` ya viene (e.g. de tests), lo
        # respetamos; sino lo poblamos desde sys.argv.
        existing = flags_dict.get('subcommands')
        if not existing:
            flags_dict['subcommands'] = positionals


def flag(flags_dict: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize flags for serverless commands.

    Contract enforced by devtools/run.py loader: name must be `flag`,
    receives raw flags dict from flags_to_dict, returns normalized dict,
    raises ValueError on validation error (loader catches + prints).
    """
    _extract_positionals(flags_dict)

    # Extraer comando posicional (primer token sin --) desde subcommands
    subcommands = flags_dict.get('subcommands', []) or []
    command = subcommands[0] if subcommands else 'help'

    if command not in VALID_COMMANDS:
        raise ValueError(
            f'Comando desconocido: {command!r}.\n'
            f'Validos: {", ".join(VALID_COMMANDS)}',
        )

    flags_dict['command'] = command

    stage = flags_dict.get('stage', 'local')
    if stage not in VALID_STAGES:
        raise ValueError(
            f'Stage invalido: {stage!r}. Validos: {", ".join(VALID_STAGES)}',
        )

    function = flags_dict.get('function')
    if function is not None and function not in VALID_FUNCTIONS:
        raise ValueError(
            f'Function invalida: {function!r}. '
            f'Validas: {", ".join(VALID_FUNCTIONS)}',
        )

    if command in DESTRUCTIVE_COMMANDS and not (
        flags_dict.get('confirm') or flags_dict.get('dry_run')
    ):
        raise ValueError(
            f'{command!r} es destructivo. Agrega --confirm o --dry-run.',
        )

    if command in PATH_REQUIRED_COMMANDS and not (
        flags_dict.get('path') or flags_dict.get('module')
    ):
        raise ValueError(
            f'{command!r} opera sobre un lambda-controller: requiere '
            f'--path=<dir> (directorio con lambda.yaml).',
        )

    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)
    flags_dict = set_default_values(flags_dict, _DEFAULTS)

    return flags_dict


def describe() -> ScriptDescribe:
    """Machine-readable inventory of serverless commands and flags."""
    return {
        'name': 'serverless',
        'kind': 'subcommand',
        'summary': (
            'Backend SAM del portfolio (Lambdas + API GW + DynamoDB + SES '
            '+ Neon) y, con --path, lambdas tipo lambda-controller'
        ),
        'commands': [
            {
                'name': cmd,
                'summary': _COMMAND_SUMMARIES.get(cmd, ''),
                'flags': _COMMAND_FLAGS.get(cmd, []),
                'destructive': cmd in DESTRUCTIVE_COMMANDS,
                'json_output': cmd in JSON_OUTPUT_COMMANDS,
            }
            for cmd in VALID_COMMANDS
        ],
        'flags': {
            'stage': {
                'type': 'choice',
                'choices': list(VALID_STAGES),
                'default': 'local',
                'summary': 'Stage del stack SAM (local|dev|prod)',
            },
            'function': {
                'type': 'choice',
                'choices': list(VALID_FUNCTIONS),
                'summary': 'Funcion Lambda objetivo',
            },
            'path': {
                'type': 'string',
                'summary': (
                    'Directorio de un lambda-controller (dir con '
                    'lambda.yaml). Activa el modo dinamico'
                ),
            },
            'event': {
                'type': 'string',
                'summary': 'Path a event JSON (events/<X>.json)',
            },
            'port': {
                'type': 'int',
                'default': 3000,
                'summary': 'Puerto local API (start-api)',
            },
            'tail': {
                'type': 'bool',
                'default': False,
                'summary': 'Continuous log streaming',
            },
            'since': {
                'type': 'string',
                'default': '10m',
                'summary': 'Ventana de logs (ej. 10m, 1h, 1d)',
            },
            'confirm': {
                'type': 'bool',
                'default': False,
                'summary': 'Confirma operacion destructiva',
            },
            'dry_run': {
                'type': 'bool',
                'default': False,
                'summary': 'Imprime acciones sin ejecutar',
            },
            'coverage_threshold': {
                'type': 'int',
                'default': 80,
                'summary': 'Threshold de coverage per-file',
            },
            'output': {
                'type': 'choice',
                'choices': ['text', 'json'],
                'default': 'text',
                'summary': 'Formato de salida',
            },
        },
    }
