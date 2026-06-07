"""Flag validation for test_runner script.

Validates and normalizes flags for the unified test runner that
orchestrates unit + coverage + typecheck tests across the project
modules (apps Astro, packages, devtools, server):
  - hub / generic / fintech / architect / leader / vibe: unit + coverage
  - pkg-*: unit + coverage para los packages del workspace
  - devtools: unit (Python 3.14)
  - server: unit (Python serverless backend)

Junio 2026: los E2E del portfolio (Playwright) ya no viven en test_runner.
Los módulos/tipos `feature`, `e2e` y `tests` fueron eliminados y se corren
con el comando dedicado `python devtools/run.py e2e --module=<api|admin|app>`.
"""

import os
import sys
from typing import Any


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


# El default del flag --env honra la env var DOCKER_ENV cuando esta seteada.
# Esto alinea test_runner con el resto de la infra del proyecto
# (.git-hooks/_common.py, scripts del CI) que usan DOCKER_ENV para indicar
# el ambiente activo (local | dev | test). Sigue pudiendo ser sobrescrito
# explicitamente con --env=...
_DEFAULT_ENV = os.environ.get('DOCKER_ENV', 'local')


_PORTFOLIO_APPS = (
    'hub',
    'generic',
    'fintech',
    'architect',
    'leader',
    'vibe',
)
_PORTFOLIO_PACKAGES = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')

# Registry of valid test types per module.
# Portfolio: apps Astro tienen unit+coverage+typecheck; tests E2E son
# globales (tests/feature/) sin módulo asignado por app.
MODULE_TEST_TYPES: dict[str, list[str]] = {
    'server': ['unit'],
    'devtools': ['unit'],
}
# Apps Astro: unit + coverage + typecheck. Los E2E del portfolio NO viven
# aqui: son Python (playwright-python + httpx) y se corren con el comando
# dedicado `python devtools/run.py e2e --module=<api|admin|app>`.
for _app in _PORTFOLIO_APPS:
    MODULE_TEST_TYPES[_app] = ['unit', 'coverage', 'typecheck']
# Packages: unit + coverage (sin typecheck dedicado, lo hace tsc del root).
for _pkg in _PORTFOLIO_PACKAGES:
    MODULE_TEST_TYPES[f'pkg-{_pkg}'] = ['unit', 'coverage']

ALLOWED_FLAGS = [
    'module',
    'type',
    'git_mode',
    'env',
    'verbose',
    'quiet',
    'skip_empty',
    'help',
]

DEFAULTS: dict[str, Any] = {
    'module': None,
    'type': 'all',
    'git_mode': None,
    'env': _DEFAULT_ENV,
    'verbose': False,
    'quiet': False,
    'skip_empty': True,
    '_invoked_from': 'cli',
}

VALID_ENVS = ['local', 'dev', 'test']


def _validate_module(flags_dict: dict[str, Any]) -> None:
    """Validate --module flag against known modules with tests.

    Mayo 2026: rechaza explicitamente ``--module=e2e`` y ``--module=tests``
    con mensaje de migración (ya no son módulos válidos; los E2E del
    portfolio viven en el módulo global ``feature``).
    """
    module = flags_dict.get('module')
    if module is None:
        return

    # Atajos históricos eliminados: dar mensaje claro de migración.
    if module in {'e2e', 'tests', 'feature'}:
        raise ValueError(
            f'--module={module} ya no existe en test_runner.\n'
            'Los E2E del portfolio son Python (playwright-python + httpx) y '
            'se corren con el comando dedicado:\n'
            '  python devtools/run.py e2e --module=<api|admin|app> --env=dev',
        )

    valid_modules = [m for m, types in MODULE_TEST_TYPES.items() if types]
    if module not in valid_modules:
        raise ValueError(
            f"Módulo inválido: '{module}'. "
            f'Módulos con tests: {", ".join(sorted(valid_modules))}',
        )


def _validate_type(flags_dict: dict[str, Any]) -> None:
    """Validate --type flag against available test types.

    'all' is always valid and means run all types for each module.
    If --module is set, validates against that module's types.
    If not, validates that at least one module supports the type.

    Mayo 2026: rechaza ``--type=e2e`` con mensaje de migración. Antes el
    tipo `e2e` solo aplicaba al módulo `e2e`; ahora los E2E del portfolio
    viven en el módulo global `feature` con `--type=feature`.
    """
    test_type = flags_dict.get('type', 'all')
    if test_type == 'all':
        return

    if test_type in {'e2e', 'feature'}:
        raise ValueError(
            f'--type={test_type} ya no existe en test_runner. '
            'Los E2E del portfolio se corren con el comando dedicado:\n'
            '  python devtools/run.py e2e --module=<api|admin|app> --env=dev',
        )

    module = flags_dict.get('module')

    if module:
        valid_types = MODULE_TEST_TYPES.get(module, [])
        if test_type not in valid_types:
            raise ValueError(
                f"Tipo '{test_type}' no disponible para '{module}'. "
                f'Tipos válidos: all, {", ".join(valid_types)}',
            )
        return

    # Without module, check that at least one module supports this type
    supporting = [
        m for m, types in MODULE_TEST_TYPES.items() if test_type in types
    ]
    if not supporting:
        all_types = sorted(
            {t for types in MODULE_TEST_TYPES.values() for t in types},
        )
        raise ValueError(
            f"Tipo '{test_type}' no disponible en ningun módulo. "
            f'Tipos válidos: all, {", ".join(all_types)}',
        )


def _validate_git_mode(flags_dict: dict[str, Any]) -> None:
    """Validate --git-mode flag."""
    git_mode = flags_dict.get('git_mode')
    if git_mode is None:
        return

    from scan.flags import get_valid_git_modes

    valid_modes = get_valid_git_modes()
    if git_mode not in valid_modes:
        raise ValueError(
            f'git-mode debe ser uno de: {", ".join(valid_modes)}. Recibido: {git_mode}',
        )


def _validate_env(flags_dict: dict[str, Any]) -> None:
    """Validate --env flag (no prod for testing)."""
    env = flags_dict.get('env', 'local')
    if env not in VALID_ENVS:
        raise ValueError(
            f"Ambiente inválido: '{env}'. "
            f'Ambientes válidos para tests: {", ".join(VALID_ENVS)}',
        )


def flag(flags_dict: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize flags for test_runner.

    Parameters
    ----------
    flags_dict : dict
        Raw flags dictionary from flags_to_dict.

    Returns
    -------
    dict
        Validated and normalized flags.

    Raises
    ------
    ValueError
        If flags are invalid.
    """
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)
    flags_dict = set_default_values(flags_dict, DEFAULTS)

    _validate_module(flags_dict)
    _validate_type(flags_dict)
    _validate_git_mode(flags_dict)
    _validate_env(flags_dict)

    if flags_dict.get('verbose'):
        print('Flags procesadas:')
        for name, value in flags_dict.items():
            if name != 'help' and not name.startswith('_') and value:
                print(f'  --{name.replace("_", "-")}: {value}')

    return flags_dict


def describe() -> ScriptDescribe:
    """Machine-readable inventory of test_runner flags."""
    return {
        'name': 'test_runner',
        'kind': 'monocommand',
        'summary': (
            'Orquestador de tests (apps Astro Vitest + packages Vitest + '
            'devtools pytest + server pytest)'
        ),
        'commands': [],
        'flags': {
            'module': {
                'type': 'choice',
                'choices': sorted(m for m, t in MODULE_TEST_TYPES.items() if t),
                'summary': 'Módulo a testear (default: todos los con tests)',
            },
            'type': {
                'type': 'choice',
                'choices': sorted(
                    {t for ts in MODULE_TEST_TYPES.values() for t in ts}
                    | {'all'}
                ),
                'default': 'all',
                'summary': 'Tipo de test a ejecutar',
            },
            'git_mode': {
                'type': 'choice',
                'choices': ['changed', 'staged', 'unstaged', 'unmerged', 'all'],
                'summary': (
                    'Filtra por estado git: usa path mirroring + per-file '
                    'coverage (server)'
                ),
            },
            'env': {
                'type': 'choice',
                'choices': list(VALID_ENVS),
                'default': _DEFAULT_ENV,
                'summary': 'Ambiente Docker',
            },
            'verbose': {
                'type': 'bool',
                'default': False,
                'summary': 'Output detallado',
            },
            'quiet': {
                'type': 'bool',
                'default': False,
                'summary': 'Silenciar salida exitosa',
            },
            'skip_empty': {
                'type': 'bool',
                'default': True,
                'summary': 'No fallar si no hay archivos cambiados',
            },
        },
    }
