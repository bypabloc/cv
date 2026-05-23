"""Flag validation and configuration for serverless CLI script.

Validates and normalizes flags for the serverless backend module. Like
``docker``, this module takes a positional subcommand (NOT `--command=`)
plus flag-based parameters. See ``.claude/rules/devtools.md`` for the
posicional-vs-flag policy.
"""

import sys
from typing import Any

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


# Stages soportados por el backend serverless. ``local`` no es un stage
# AWS real — apunta a la ejecucion local del Lambda (RIE / modo directo).
VALID_STAGES = ['local', 'dev', 'stage', 'prod']

STAGE_DESCRIPTIONS = {
    'local': 'Ejecucion local del Lambda (RIE / modo directo, sin AWS)',
    'dev': 'Recursos provisionados en us-east-1 (cuenta dev / sandbox)',
    'stage': 'Recursos de pre-produccion en us-east-1 (replica prod)',
    'prod': 'Recursos provisionados en us-east-1 (cuenta productiva)',
}

# Tipos de test soportados por el comando `tests`.
VALID_TEST_TYPES = ['unit', 'integration', 'coverage']

# Modos de ejecucion local del comando `run --stage=local`.
VALID_RUNTIME_MODES = ['rie', 'direct']

VALID_COMMANDS = [
    # Setup / Maintenance
    'init',  # uv sync + verifica aws CLI + uv
    'clean',  # rm caches + artefactos efimeros (build/, core/shared)
    # Quality (Ruff + mypy sobre serverless/lambda/shared/ y serverless/lambda/services/)
    'lint',  # Ruff check
    'lint-fix',  # Ruff check --fix
    'lint-deps',  # Valida la regla de dedup D-3 (deps lambda vs shared/)
    'detect-changes',  # Detecta lambdas afectados entre 2 shas (CI)
    'format',  # Ruff format
    'typecheck',  # mypy
    # Tests: unico comando, --type=unit|integration|coverage + target
    'tests',  # pytest de un lambda (--lambda), shared (--shared) o todo
    # lambda-controller: ciclo de vida de cada Lambda con AWS CLI directo.
    'run',  # ejecuta un lambda: --stage=local -> RIE/directo; resto -> aws invoke
    'deploy',  # provisiona el lambda en un stage (AWS CLI + estado local)
    'destroy',  # borra los recursos de un stage (lambda(s) + infra)
    'status',  # estado local vs AWS, por scope
    # Infra: recursos compartidos provisionados con AWS CLI directo
    'provision-infra',  # provisiona TODOS los recursos de resources/
    'list-resources',  # lista los recursos declarados en resources/
    # Secrets / Setup AWS resources fuera del template
    'setup-ssm',  # Crear SSM Parameters (turnstile-secret, neon-url)
    'rotate-secret',  # Rotar valor de un SSM Parameter
    'sync-secrets',  # Sync .env del stage -> SSM (idempotente, hash-based)
    'secrets-status',  # .env vs SSM por entrada del catalogo (sin valores)
    'validate-catalog',  # Valida resources/secrets/*.yaml
    'verify-ses-dns',  # dig DKIM/SPF/DMARC contra Cloudflare
    'request-ses-prod',  # Imprime plantilla del ticket SES production access
    # Observability
    'metrics',  # CloudWatch metrics summary del stack
    'alarms',  # Lista alarmas y su estado
    # Rate-limit management (alternativa $0 a AWS WAF)
    'rate-limit',  # Dispatcher: list|show|set|allow|block|unblock|stats|clear-buckets
    'help',  # Ayuda colorizada
]

# Flags aceptados (validados en validate_allowed_flags). El handler usa
# solo los relevantes a su subcomando.
ALLOWED_FLAGS = [
    # Stage
    'stage',
    # lambda-controller: como apuntar al lambda objetivo
    'lambda',  # --lambda=<nombre> resuelto contra serverless/lambda/services/* (recomendado)
    'path',  # --path=<dir> del lambda (dir con manifest.yaml, cualquier ubicacion)
    'module',  # alias de --path
    'shared',  # --shared o --shared=<subpaquete> (target del comando tests)
    # Deploy / run
    'confirm',  # required para comandos destructivos
    'yes',  # confirmacion no interactiva de `destroy`
    'event',  # --event=events/<X>.json (run)
    'runtime_mode',  # --runtime-mode=rie|direct (run --stage=local)
    # Quality / Tests
    'module_path',  # Subset del codigo (ej. src/contact_form/)
    'files',  # Subset de archivos especificos
    'verbose',
    'v',  # alias de verbose
    'quiet',
    'output_format',
    # Test
    'type',  # --type=unit|integration|coverage (comando tests)
    'coverage_threshold',  # default 80
    # Secrets
    'name',  # --name=/portfolio/turnstile-secret
    'value',  # --value=... (preferir leer de stdin para no leak shell history)
    'key_id',  # --key-id=alias/portfolio-lambdas
    'only',  # --only=turnstile-secret,neon-url (subset del catalogo)
    # detect-changes (CI)
    'base',  # --base=<sha> SHA base del diff
    'head',  # --head=<sha> SHA head del diff (default HEAD)
    # Cross-cutting
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
    'since',  # --since=10m|1h|24h (ventana de metrics / rate-limit stats)
    'aws_profile',  # --aws-profile=tfs-dev (perfil AWS CLI)
    # Internal
    'command',
    'subcommands',
    'help',
]


# Comandos destructivos. Cada uno requiere --confirm o --dry-run primero.
# `destroy` NO esta aqui: usa su propio flag --yes (validado en cmd_destroy).
DESTRUCTIVE_COMMANDS = frozenset(
    {
        'clean',
        'rotate-secret',
    }
)


# Comandos del modo lambda-controller: requieren apuntar a un lambda con
# --lambda=<nombre> (resuelto contra serverless/lambda/services/*) o --path=<dir>.
# `tests` NO esta aqui: sin target corre toda la suite, o usa --shared.
# `destroy` / `status` NO estan: sin --lambda operan sobre todo el stage.
PATH_REQUIRED_COMMANDS = frozenset(
    {
        'run',
        'deploy',
    }
)


# Comandos que soportan --output=json para integracion CI/scripts.
JSON_OUTPUT_COMMANDS = frozenset(
    {
        'metrics',
        'alarms',
    }
)


# Resumenes 1-line por comando (usados por describe() y help).
_COMMAND_SUMMARIES: dict[str, str] = {
    'init': 'Setup inicial (uv sync + verifica AWS CLI + uv)',
    'clean': 'Eliminar caches + artefactos efimeros (build/, vendor)',
    'lint': 'Ruff check sobre shared/ y src/',
    'lint-fix': 'Ruff check --fix',
    'lint-deps': 'Valida que un lambda no duplique deps de shared/ (D-3)',
    'format': 'Ruff format',
    'typecheck': 'mypy strict sobre shared/ y src/',
    'tests': 'pytest --type=unit|integration|coverage (--lambda / --shared)',
    'run': 'Ejecuta un lambda: --stage=local -> RIE/directo; resto -> aws invoke',
    'deploy': 'Provisiona el lambda en un stage (AWS CLI + estado local)',
    'destroy': 'Borra los recursos de un stage (lambda(s) + infra) — requiere --yes',
    'status': 'Estado local vs AWS, por scope',
    'provision-infra': 'Provisiona TODOS los recursos de resources/ con AWS CLI',
    'list-resources': 'Lista los recursos declarados en resources/',
    'setup-ssm': 'Crear SSM Parameters con KMS (turnstile, neon-url)',
    'rotate-secret': 'Rotar valor de un SSM Parameter (DESTRUCTIVO)',
    'sync-secrets': 'Sync .env del stage -> SSM (idempotente, hash-based)',
    'secrets-status': '.env vs SSM por entrada del catalogo (sin valores)',
    'validate-catalog': 'Valida resources/secrets/*.yaml',
    'verify-ses-dns': 'dig CNAMEs DKIM + TXT SPF/DMARC vs Cloudflare',
    'request-ses-prod': 'Plantilla del ticket de production access SES',
    'metrics': 'Resumen CloudWatch metrics del stack',
    'alarms': 'Lista alarmas + estado',
    'rate-limit': 'Gestion de reglas rate-limit (list|set|allow|block|stats|...)',
    'help': 'Ayuda colorizada',
}


# Flags relevantes por comando (informativo para describe() y completion).
_COMMAND_FLAGS: dict[str, list[str]] = {
    'init': [],
    'clean': ['dry_run'],
    'lint': ['module_path', 'files', 'output_format'],
    'lint-fix': ['module_path', 'files'],
    'lint-deps': ['lambda', 'path', 'module'],
    'format': ['module_path', 'files'],
    'typecheck': ['module_path'],
    'tests': [
        'type',
        'lambda',
        'path',
        'module',
        'shared',
        'verbose',
        'coverage_threshold',
    ],
    'run': [
        'lambda',
        'path',
        'module',
        'stage',
        'event',
        'runtime_mode',
        'aws_profile',
    ],
    'deploy': [
        'lambda',
        'path',
        'module',
        'stage',
        'aws_profile',
        'dry_run',
        'skip_sync',
    ],
    'destroy': ['lambda', 'path', 'module', 'stage', 'yes', 'aws_profile'],
    'status': ['lambda', 'path', 'module', 'stage', 'aws_profile'],
    'provision-infra': ['stage', 'aws_profile', 'dry_run'],
    'list-resources': ['stage'],
    'setup-ssm': ['stage', 'name', 'value', 'key_id', 'aws_profile'],
    'rotate-secret': ['stage', 'name', 'value', 'confirm', 'aws_profile'],
    'sync-secrets': ['stage', 'only', 'aws_profile', 'dry_run'],
    'secrets-status': ['stage', 'aws_profile', 'output'],
    'validate-catalog': [],
    'verify-ses-dns': [],
    'request-ses-prod': [],
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
    'help': [],
}


# Defaults aplicados por set_default_values cuando un flag no se provee.
_DEFAULTS: dict[str, Any] = {
    'stage': 'local',
    'confirm': False,
    'yes': False,
    'runtime_mode': 'rie',
    'since': '10m',
    'verbose': False,
    'quiet': False,
    'output_format': 'text',
    'coverage_threshold': 80,
    'dry_run': False,
    'skip_sync': False,
    'output': 'text',
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

    if command in DESTRUCTIVE_COMMANDS and not (
        flags_dict.get('confirm') or flags_dict.get('dry_run')
    ):
        raise ValueError(
            f'{command!r} es destructivo. Agrega --confirm o --dry-run.',
        )

    if command in PATH_REQUIRED_COMMANDS and not (
        flags_dict.get('lambda')
        or flags_dict.get('path')
        or flags_dict.get('module')
    ):
        raise ValueError(
            f'{command!r} opera sobre un lambda-controller: requiere '
            f'--lambda=<nombre> (resuelto contra serverless/lambda/services/*) '
            f'o --path=<dir> (directorio con manifest.yaml).',
        )

    if command == 'tests':
        test_type = flags_dict.get('type')
        if test_type not in VALID_TEST_TYPES:
            raise ValueError(
                'tests requiere --type=unit|integration|coverage '
                f'(recibido: {test_type!r}).',
            )

    runtime_mode = flags_dict.get('runtime_mode')
    if runtime_mode is not None and runtime_mode not in VALID_RUNTIME_MODES:
        raise ValueError(
            f'--runtime-mode invalido: {runtime_mode!r}. '
            f'Validos: {", ".join(VALID_RUNTIME_MODES)}.',
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
            'Backend serverless del portfolio: infra compartida + 4 Lambdas '
            'lambda-controller, provisionados con AWS CLI directo (sin SAM). '
            'Cada Lambda se opera con --lambda=<nombre>'
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
                'summary': 'Stage objetivo (local|dev|prod)',
            },
            'lambda': {
                'type': 'string',
                'summary': (
                    'Nombre corto de un lambda, resuelto contra '
                    'serverless/lambda/services/<nombre>/. Forma recomendada de '
                    'apuntar a un lambda-controller'
                ),
            },
            'path': {
                'type': 'string',
                'summary': (
                    'Directorio de un lambda (dir con manifest.yaml), '
                    'cualquier ubicacion. Alternativa a --lambda'
                ),
            },
            'event': {
                'type': 'string',
                'summary': 'Path a event JSON (events/<X>.json)',
            },
            'runtime_mode': {
                'type': 'choice',
                'choices': list(VALID_RUNTIME_MODES),
                'default': 'rie',
                'summary': (
                    'Modo de ejecucion local (run --stage=local): rie '
                    '(Runtime Interface Emulator via Docker) o direct '
                    '(importa el handler en el proceso)'
                ),
            },
            'yes': {
                'type': 'bool',
                'default': False,
                'summary': 'Confirmacion no interactiva de `destroy`',
            },
            'type': {
                'type': 'choice',
                'choices': list(VALID_TEST_TYPES),
                'summary': (
                    'Tipo de test para el comando tests '
                    '(unit | integration | coverage)'
                ),
            },
            'shared': {
                'type': 'string',
                'summary': (
                    'Target del comando tests: --shared para toda la '
                    'libreria comun, --shared=<subpaquete> para uno solo'
                ),
            },
            'aws_profile': {
                'type': 'string',
                'summary': (
                    'Perfil AWS CLI a inyectar en los comandos aws '
                    '(ej. --aws-profile=tfs-dev). Si se omite, se usa el '
                    'perfil por defecto (AWS_PROFILE o [default])'
                ),
            },
            'since': {
                'type': 'string',
                'default': '10m',
                'summary': 'Ventana de metrics / rate-limit stats (10m, 1h)',
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
            'skip_sync': {
                'type': 'bool',
                'default': False,
                'summary': 'Saltar sync de secretos al desplegar',
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
