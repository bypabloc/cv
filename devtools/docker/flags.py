"""Flag validation and configuration for Docker CLI script.

Validates and normalizes flags for docker commands.
Handles positional subcommand extraction and environment validation.
"""

import sys

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


VALID_ENVS = ['local', 'dev', 'test', 'prod']

ENV_DESCRIPTIONS = {
    'local': 'Desarrollo local con hot reload',
    'dev': 'Desarrollo remoto (codigo en imagen)',
    'test': 'Ambiente de testing aislado',
    'prod': 'Producción con Gunicorn',
}

COMPOSE_FILES = {
    'local': 'docker-compose/local.yml',
    'dev': 'docker-compose/dev.yml',
    'test': 'docker-compose/test.yml',
    'prod': 'docker-compose/prod.yml',
}

VALID_COMMANDS = [
    # Lifecycle
    'up',
    'down',
    'build',
    'rebuild',
    'logs',
    'shell',
    'exec',
    'ps',
    'restart',
    'refresh',
    # Django
    'migrate',
    'makemigrations',
    'createsuperuser',
    'manage',
    # Quality
    'lint',
    'lint-fix',
    'format',
    'test',
    # Database
    'db-shell',
    'db-tables',
    'db-describe',
    'db-count',
    'db-seed',
    'db-reset',
    # Setup
    'setup',
    'clean',
    'help',
    # Cache
    'cache-clear-all',
    'cache-status',
]

ALLOWED_FLAGS = [
    # Environment
    'env',
    # Lifecycle
    'detach',
    'build',
    'volumes',
    'no_cache',
    'clean',
    # Service / Profile (subset rebuilds, on-demand profiles)
    'service',
    'profile',
    # Logs
    'tail',
    'follow',
    'w',
    # Exec
    'target',
    # Test / Lint
    'type',
    'module',
    'quiet',
    'files',
    'verbose',
    'v',
    'output_format',
    # Database
    'clear',
    'only',
    'table',
    # Setup
    'no_seed',
    'no_superuser',
    # Refresh
    'keep_volumes',
    'skip_cache',
    # Cross-cutting
    'dry_run',
    'output',
    # Internal
    'command',
    'subcommands',
]

# Compose services known to be gated behind a profile (only started on demand)
PROFILE_SERVICES = {
    'e2e': 'e2e',
}


# Commands that mutate state irreversibly. Each accepts ``--dry-run`` to
# print actions without executing them.
DESTRUCTIVE_COMMANDS = frozenset(
    {'rebuild', 'refresh', 'clean', 'db-reset', 'db-seed'}
)


# Commands that support ``--output=json`` for machine-readable output.
JSON_OUTPUT_COMMANDS = frozenset(
    {'ps', 'db-tables', 'db-count', 'cache-status'}
)


# Per-command summaries (used by describe() and the colourised help). Keep in
# the same order as VALID_COMMANDS so contributors see drift immediately.
_COMMAND_SUMMARIES: dict[str, str] = {
    'up': 'Levantar servicios',
    'down': 'Detener servicios',
    'build': 'Construir imágenes',
    'rebuild': 'Reconstruir desde cero (down + build --no-cache + up)',
    'logs': 'Ver logs de servicios',
    'shell': 'Bash interactivo en server',
    'exec': 'Ejecutar comando en container',
    'ps': 'Listar containers',
    'restart': 'Reiniciar servicios',
    'refresh': 'Refresh completo (down + caches + up + migrate)',
    'migrate': 'Ejecutar migraciones Django',
    'makemigrations': 'Generar migraciones Django',
    'createsuperuser': 'Crear superusuario (usa env vars)',
    'manage': 'Pass-through a manage.py',
    'lint': 'Lint (Ruff server, Biome dashboard/landing)',
    'lint-fix': 'Lint con auto-fix',
    'format': 'Format (Ruff/Biome)',
    'test': 'Removido — usa test_runner',
    'db-shell': 'Abrir psql interactivo',
    'db-tables': 'Listar tablas',
    'db-describe': 'Describir tabla',
    'db-count': 'Conteo de filas por tabla',
    'db-seed': 'Ejecutar seeds',
    'db-reset': 'Reset completo de DB (destructivo)',
    'setup': 'Setup inicial completo',
    'clean': 'Eliminar todo (containers + images + volumes)',
    'help': 'Mostrar ayuda colorizada',
    'cache-clear-all': 'Limpiar todos los caches',
    'cache-status': 'Ver estado de caches',
}


# Per-command relevant flags (informative; the runtime accepts any flag in
# ALLOWED_FLAGS but this lets describe() and shell completion suggest only
# what is meaningful per command).
_COMMAND_FLAGS: dict[str, list[str]] = {
    'up': ['env', 'detach', 'build', 'service', 'profile'],
    'down': ['env', 'volumes'],
    'build': ['env', 'no_cache', 'service', 'profile'],
    'rebuild': ['env', 'service', 'profile', 'dry_run'],
    'logs': ['env', 'tail', 'follow'],
    'shell': ['env'],
    'exec': ['env', 'target'],
    'ps': ['env', 'output'],
    'restart': ['env'],
    'refresh': ['env', 'keep_volumes', 'skip_cache', 'dry_run'],
    'migrate': ['env'],
    'makemigrations': ['env'],
    'createsuperuser': ['env'],
    'manage': ['env'],
    'lint': ['env', 'module', 'files', 'output_format'],
    'lint-fix': ['env', 'module', 'files'],
    'format': ['env', 'module', 'files'],
    'test': [],
    'db-shell': ['env'],
    'db-tables': ['env', 'output'],
    'db-describe': ['env'],
    'db-count': ['env', 'output'],
    'db-seed': ['env', 'clear', 'only', 'dry_run'],
    'db-reset': ['env', 'no_seed', 'no_superuser', 'dry_run'],
    'setup': ['env', 'no_seed', 'no_superuser'],
    'clean': ['env', 'dry_run'],
    'help': [],
    'cache-clear-all': ['env'],
    'cache-status': ['env', 'output'],
}


def describe() -> ScriptDescribe:
    """Machine-readable inventory of docker commands and flags."""
    return {
        'name': 'docker',
        'kind': 'subcommand',
        'summary': 'Gestion de Docker multi-ambiente',
        'commands': [
            {
                'name': cmd,
                'summary': _COMMAND_SUMMARIES.get(cmd, ''),
                'flags': _COMMAND_FLAGS.get(cmd, []),
                'destructive': cmd in DESTRUCTIVE_COMMANDS,
                'deprecated': cmd == 'test',
            }
            for cmd in VALID_COMMANDS
        ],
        'flags': {
            'env': {
                'type': 'choice',
                'choices': list(VALID_ENVS),
                'default': 'local',
                'summary': 'Ambiente Docker',
            },
            'detach': {
                'type': 'bool',
                'default': True,
                'summary': 'Levantar en background (default)',
            },
            'build': {
                'type': 'bool',
                'default': False,
                'summary': 'Rebuild antes de up',
            },
            'volumes': {
                'type': 'bool',
                'default': False,
                'summary': 'Eliminar volumes (down --volumes)',
            },
            'no_cache': {
                'type': 'bool',
                'default': False,
                'summary': 'Build sin cache',
            },
            'service': {
                'type': 'string',
                'summary': 'Limitar a un servicio (auto-resuelve profile)',
            },
            'profile': {
                'type': 'string',
                'summary': 'Profile compose (e2e on-demand)',
            },
            'tail': {
                'type': 'int',
                'default': 50,
                'summary': 'Lineas a mostrar en logs',
            },
            'follow': {
                'type': 'bool',
                'default': False,
                'summary': 'Seguir logs (logs --follow)',
            },
            'target': {
                'type': 'string',
                'default': 'server',
                'summary': 'Container destino para exec',
            },
            'module': {
                'type': 'choice',
                'choices': [
                    'server',
                    'devtools',
                    'hub',
                    'generic',
                    'fintech',
                    'architect',
                    'leader',
                    'vibe',
                    'pkg-app-shared',
                    'pkg-content',
                    'pkg-cv-pdf',
                    'pkg-seo',
                    'pkg-ui',
                ],
                'default': 'server',
                'summary': 'Módulo a procesar',
            },
            'files': {
                'type': 'string',
                'summary': 'Archivos especificos (separados por espacio o ;)',
            },
            'output_format': {
                'type': 'choice',
                'choices': ['console', 'json'],
                'default': 'console',
                'summary': 'Formato de salida (lint solo)',
            },
            'clear': {
                'type': 'bool',
                'default': False,
                'summary': 'db-seed con clear previo',
            },
            'only': {
                'type': 'string',
                'summary': 'Cargar solo fixtures especificos (db-seed)',
            },
            'no_seed': {
                'type': 'bool',
                'default': False,
                'summary': 'Skip seeds en setup/db-reset',
            },
            'no_superuser': {
                'type': 'bool',
                'default': False,
                'summary': 'Skip createsuperuser en setup/db-reset',
            },
            'keep_volumes': {
                'type': 'bool',
                'default': False,
                'summary': 'Preservar volumes en refresh',
            },
            'skip_cache': {
                'type': 'bool',
                'default': False,
                'summary': 'Skip clear de pycache en refresh',
            },
            'dry_run': {
                'type': 'bool',
                'default': False,
                'summary': 'Imprime acciones sin ejecutar (destructivos)',
            },
            'output': {
                'type': 'choice',
                'choices': ['text', 'json'],
                'default': 'text',
                'summary': 'Formato global de salida (donde aplique)',
            },
        },
    }


def _extract_command(flags_dict: dict) -> None:
    """Extract positional command from sys.argv into flags_dict.

    Error explicito si no se pasa comando: el viejo default 'help' era
    confuso porque tapaba errores de tipeo (ej: ``docker --env=local``
    sin comando). El usuario ahora ve el error y se le pide ``docker
    help`` (texto colorizado) o ``docker --help`` (README).

    Pasa todo lo que sigue a ``--`` (separador POSIX) directo a
    ``subcommands``, así ``docker exec --target=server -- echo hi`` y
    ``docker manage migrate -- --plan --verbosity=2`` funcionan sin que
    el validador rechace los flags del subproceso.
    """
    # Argumentos posicionales: todo antes de '--' (separador POSIX) que no
    # sea una flag. Después de '--' viene en flags_dict['_passthrough'] via
    # flags_to_dict, lo concatenamos al final de subcommands.
    raw_args = sys.argv[2:]
    pre_double_dash: list[str] = []
    for arg in raw_args:
        if arg == '--':
            break
        if not arg.startswith('--'):
            pre_double_dash.append(arg)

    passthrough = flags_dict.pop('_passthrough', None) or []

    if pre_double_dash:
        flags_dict['command'] = pre_double_dash[0]
        flags_dict['subcommands'] = [*pre_double_dash[1:], *passthrough]
    else:
        raise ValueError(
            'Falta el comando. '
            'Ejecuta `docker help` (texto colorizado) o `docker --help` '
            '(README) para ver los comandos disponibles.\n'
            f'Comandos válidos: {", ".join(VALID_COMMANDS)}'
        )

    command = flags_dict['command']
    if command not in VALID_COMMANDS:
        raise ValueError(
            f"Comando desconocido: '{command}'\n"
            f'Comandos válidos: {", ".join(VALID_COMMANDS)}'
        )


_PORTFOLIO_APPS = (
    'hub',
    'generic',
    'fintech',
    'architect',
    'leader',
    'vibe',
)
_PORTFOLIO_PACKAGES = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')
_FRONTEND_MODULES = (
    *_PORTFOLIO_APPS,
    *(f'pkg-{p}' for p in _PORTFOLIO_PACKAGES),
)


def _validate_module(flags_dict: dict) -> None:
    """Validate --module flag for test/lint/format commands.

    Portfolio: módulos válidos son las 6 apps Astro (hub, generic, ...)
    y los packages como `pkg-<name>`, además de server/devtools.
    """
    command = flags_dict['command']

    if command == 'test':
        valid_modules = ['all', 'server', *_FRONTEND_MODULES]
        module = flags_dict.get('module', 'all')
        if module not in valid_modules:
            raise ValueError(
                f"Módulo inválido: '{module}'\n"
                f'Módulos válidos para test: {", ".join(valid_modules)}'
            )

    if command in ('lint', 'lint-fix', 'format'):
        valid_modules = ['server', 'devtools', *_FRONTEND_MODULES]
        if flags_dict.get('module') in (None, 'all'):
            flags_dict['module'] = 'server'
        module = flags_dict['module']
        if module not in valid_modules:
            raise ValueError(
                f"Módulo inválido: '{module}'\n"
                f'Módulos válidos para {command}: {", ".join(valid_modules)}'
            )

    # output-format: solo para lint + server
    output_format = flags_dict.get('output_format', 'console')
    if output_format != 'console':
        valid_formats = ['console', 'json']
        if output_format not in valid_formats:
            raise ValueError(
                f"Formato inválido: '{output_format}'\n"
                f'Formatos válidos: {", ".join(valid_formats)}'
            )
        if command != 'lint':
            raise ValueError(
                f'--output-format solo aplica al comando lint, no a {command}'
            )
        if flags_dict.get('module', 'server') in _FRONTEND_MODULES:
            raise ValueError(
                '--output-format=json solo soportado para --module=server (Ruff)'
            )


def flag(flags_dict: dict) -> dict:
    """Validate and normalize flags for docker commands.

    Parameters
    ----------
    flags_dict : dict
        Raw flags dictionary from flags_to_dict

    Returns
    -------
    dict
        Validated and normalized flags dictionary

    Raises
    ------
    ValueError
        If command or environment is invalid
    """
    _extract_command(flags_dict)
    try:
        validate_allowed_flags(flags_dict, ALLOWED_FLAGS)
    except ValueError as exc:
        # Mensaje util cuando el usuario quiso pasar flags al subproceso (manage,
        # exec) y olvido el separador POSIX. Conservamos el error original como
        # contexto y agregamos la pista; otros comandos siguen viendo el error
        # estándar de "Flags no permitidas: ...".
        if flags_dict.get('command') in ('manage', 'exec'):
            cmd = flags_dict['command']
            example = (
                f'docker {cmd} <subcommand> -- <flags-del-subproceso>'
                if cmd == 'manage'
                else f'docker {cmd} --target=<service> -- <comando-y-flags>'
            )
            raise ValueError(
                f'{exc}\n\n'
                f"Hint: '{cmd}' delega al subproceso. Para pasarle flags "
                'desconocidos al CLI, usa el separador POSIX `--`:\n'
                f'    {example}'
            ) from exc
        raise

    env = flags_dict.get('env', 'local')
    if env not in VALID_ENVS:
        raise ValueError(
            f"Ambiente inválido: '{env}'\nAmbientes válidos: {', '.join(VALID_ENVS)}"
        )

    flags_dict = set_default_values(
        flags_dict,
        {
            'env': 'local',
            'detach': True,
            'tail': '50',
            'follow': flags_dict.get('w', False),
            'target': 'server',
            'type': 'all',
            'module': 'all',
            'quiet': False,
            'verbose': flags_dict.get('v', False),
            'output_format': 'console',
            'dry_run': False,
            'output': 'text',
        },
    )

    _validate_module(flags_dict)

    if isinstance(flags_dict.get('tail'), str):
        try:
            flags_dict['tail'] = int(flags_dict['tail'])
        except ValueError:
            flags_dict['tail'] = 50

    return flags_dict
