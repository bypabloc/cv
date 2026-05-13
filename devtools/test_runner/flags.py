"""Flag validation for test_runner script.

Validates and normalizes flags for the unified test runner that
orchestrates tests across all project modules (server, dashboard, landing,
devtools).

Mayo 2026: el modulo `e2e` y el tipo `--type=e2e` fueron eliminados.
Ahora cada modulo expone su propio `--type=feature` (BDD-style):
  - server: pytest -m feature contra tests/feature/ (DRF APIClient + DB seed)
  - dashboard: Playwright contra dashboard/tests/feature/
  - landing:   Playwright contra landing/tests/feature/
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
# globales (tests/feature/) sin modulo asignado por app.
MODULE_TEST_TYPES: dict[str, list[str]] = {
    'server': ['unit'],
    'devtools': ['unit'],
}
# Apps Astro: unit + coverage + typecheck (sin feature individual; los E2E
# son globales en tests/feature/).
for _app in _PORTFOLIO_APPS:
    MODULE_TEST_TYPES[_app] = ['unit', 'coverage', 'typecheck']
# Packages: unit + coverage (sin typecheck dedicado, lo hace tsc del root).
for _pkg in _PORTFOLIO_PACKAGES:
    MODULE_TEST_TYPES[f'pkg-{_pkg}'] = ['unit', 'coverage']
# E2E global del portfolio (Playwright):
MODULE_TEST_TYPES['feature'] = ['feature']

ALLOWED_FLAGS = [
    'module',
    'type',
    'git_mode',
    'env',
    'verbose',
    'quiet',
    'skip_empty',
    'screenshots',
    'ui_review',
    'project',
    'shard',
    'shard_total',
    'fail_on_flaky',
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
    'screenshots': False,
    'ui_review': False,
    'project': '',
    'shard': None,
    'shard_total': None,
    'fail_on_flaky': False,
    '_invoked_from': 'cli',
}

VALID_ENVS = ['local', 'dev', 'test']


def _validate_module(flags_dict: dict[str, Any]) -> None:
    """Validate --module flag against known modules with tests.

    Mayo 2026: rechaza explicitamente ``--module=e2e`` y ``--module=tests``
    con mensaje de migracion (ya no son modulos validos; cada feature
    test vive bajo el modulo de su producto: dashboard, landing, server).
    """
    module = flags_dict.get('module')
    if module is None:
        return

    # Atajos historicos eliminados: dar mensaje claro de migracion.
    if module in {'e2e', 'tests'}:
        raise ValueError(
            f'--module={module} fue eliminado en mayo 2026.\n'
            'Usa el modulo del producto y --type=feature:\n'
            '  python devtools/run.py test_runner --module=dashboard --type=feature\n'
            '  python devtools/run.py test_runner --module=landing --type=feature\n'
            '  python devtools/run.py test_runner --module=server --type=feature',
        )

    valid_modules = [m for m, types in MODULE_TEST_TYPES.items() if types]
    if module not in valid_modules:
        raise ValueError(
            f"Modulo invalido: '{module}'. "
            f'Modulos con tests: {", ".join(sorted(valid_modules))}',
        )


def _validate_type(flags_dict: dict[str, Any]) -> None:
    """Validate --type flag against available test types.

    'all' is always valid and means run all types for each module.
    If --module is set, validates against that module's types.
    If not, validates that at least one module supports the type.

    Mayo 2026: rechaza ``--type=e2e`` con mensaje de migracion. Antes el
    tipo `e2e` solo aplicaba al modulo `e2e`; ahora cada producto tiene
    su `--type=feature` (BDD-style).
    """
    test_type = flags_dict.get('type', 'all')
    if test_type == 'all':
        return

    if test_type == 'e2e':
        raise ValueError(
            '--type=e2e fue eliminado en mayo 2026. '
            'Usa --type=feature por modulo:\n'
            '  python devtools/run.py test_runner --module=dashboard --type=feature\n'
            '  python devtools/run.py test_runner --module=landing --type=feature\n'
            '  python devtools/run.py test_runner --module=server --type=feature',
        )

    module = flags_dict.get('module')

    if module:
        valid_types = MODULE_TEST_TYPES.get(module, [])
        if test_type not in valid_types:
            raise ValueError(
                f"Tipo '{test_type}' no disponible para '{module}'. "
                f'Tipos validos: all, {", ".join(valid_types)}',
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
            f"Tipo '{test_type}' no disponible en ningun modulo. "
            f'Tipos validos: all, {", ".join(all_types)}',
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
            f"Ambiente invalido: '{env}'. "
            f'Ambientes validos para tests: {", ".join(VALID_ENVS)}',
        )


def _validate_feature_flags(flags_dict: dict[str, Any]) -> None:
    """Validate --screenshots and --ui-review require feature context.

    Estos flags solo aplican a Playwright (feature tests de dashboard/landing).
    Si ``--module=server --type=feature`` los usa, error: pytest no genera
    screenshots ni alimenta el UI review.
    """
    screenshots = flags_dict.get('screenshots', False)
    ui_review = flags_dict.get('ui_review', False)

    if not screenshots and not ui_review:
        return

    module = flags_dict.get('module')
    test_type = flags_dict.get('type', 'all')

    is_playwright_feature = module == 'feature' and test_type == 'feature'
    if not is_playwright_feature:
        flag_name = '--screenshots' if screenshots else '--ui-review'
        raise ValueError(
            f'{flag_name} requiere --module=dashboard|landing y --type=feature '
            '(solo Playwright soporta screenshots).',
        )

    if ui_review and not screenshots:
        flags_dict['screenshots'] = True


def _coerce_int(flags_dict: dict[str, Any], key: str) -> None:
    """Convierte el flag de str a int si es no-None y string."""
    value = flags_dict.get(key)
    if value is None or isinstance(value, int):
        return
    try:
        flags_dict[key] = int(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f'--{key.replace("_", "-")} debe ser un entero. Recibido: {value!r}',
        ) from exc


def _validate_playwright_only_flag(
    flags_dict: dict[str, Any],
    key: str,
    present: bool,
) -> None:
    """Valida que un flag de Playwright (sharding/projects) no se use con
    server o con --type distinto de feature.

    Sharding y projects son features de Playwright, asi que requieren
    --module=dashboard|landing y --type=feature.
    """
    if not present:
        return
    module = flags_dict.get('module')
    test_type = flags_dict.get('type', 'all')
    is_playwright_feature = module == 'feature' and test_type == 'feature'
    if not is_playwright_feature:
        raise ValueError(
            f'--{key.replace("_", "-")} requiere '
            '--module=dashboard|landing y --type=feature',
        )


def _validate_sharding_flags(flags_dict: dict[str, Any]) -> None:
    """Valida --project, --shard, --shard-total, --fail-on-flaky.

    Reglas:
    - Las 4 flags requieren --module=dashboard|landing y --type=feature
    - --shard y --shard-total deben usarse juntos
    - shard y shard_total son enteros >= 1
    - shard <= shard_total
    """
    _coerce_int(flags_dict, 'shard')
    _coerce_int(flags_dict, 'shard_total')

    project = flags_dict.get('project') or ''
    shard = flags_dict.get('shard')
    shard_total = flags_dict.get('shard_total')
    fail_on_flaky = flags_dict.get('fail_on_flaky', False)

    _validate_playwright_only_flag(flags_dict, 'project', bool(project))
    _validate_playwright_only_flag(flags_dict, 'shard', shard is not None)
    _validate_playwright_only_flag(
        flags_dict,
        'shard_total',
        shard_total is not None,
    )
    _validate_playwright_only_flag(
        flags_dict,
        'fail_on_flaky',
        bool(fail_on_flaky),
    )

    if shard is not None and shard_total is None:
        raise ValueError('--shard requiere --shard-total')
    if shard_total is not None and shard is None:
        raise ValueError('--shard-total requiere --shard')

    if shard is not None and shard < 1:
        raise ValueError('--shard debe ser >= 1')
    if shard_total is not None and shard_total < 1:
        raise ValueError('--shard-total debe ser >= 1')

    if shard is not None and shard_total is not None and shard > shard_total:
        raise ValueError(
            f'--shard ({shard}) no puede exceder --shard-total ({shard_total})',
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
    _validate_feature_flags(flags_dict)
    _validate_sharding_flags(flags_dict)

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
            'Orquestador de tests (server pytest, dashboard+landing Vitest, '
            'feature: Playwright en frontend / DRF APIClient en server)'
        ),
        'commands': [],
        'flags': {
            'module': {
                'type': 'choice',
                'choices': sorted(m for m, t in MODULE_TEST_TYPES.items() if t),
                'summary': 'Modulo a testear (default: todos los con tests)',
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
            'screenshots': {
                'type': 'bool',
                'default': False,
                'summary': (
                    'Generar screenshots durante --type=feature '
                    '(solo dashboard/landing)'
                ),
            },
            'ui_review': {
                'type': 'bool',
                'default': False,
                'summary': (
                    'Revisar screenshots con Gemini CLI tras feature tests '
                    '(solo dashboard/landing)'
                ),
            },
            'project': {
                'type': 'string',
                'summary': (
                    'Project Playwright (feature tests: desktop-chromium, '
                    'desktop-webkit, mobile-chromium, mobile-webkit, etc.)'
                ),
            },
            'shard': {
                'type': 'int',
                'summary': (
                    'Shard index 1-based (requiere shard_total). '
                    'Solo aplica a --type=feature en dashboard/landing.'
                ),
            },
            'shard_total': {
                'type': 'int',
                'summary': 'Total de shards (solo --type=feature)',
            },
            'fail_on_flaky': {
                'type': 'bool',
                'default': False,
                'summary': (
                    'Pasa --fail-on-flaky-tests a Playwright '
                    '(solo --type=feature)'
                ),
            },
        },
    }
