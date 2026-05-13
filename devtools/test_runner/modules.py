"""Module/test-type resolution for the test_runner."""

from __future__ import annotations

from typing import Any

from test_runner.flags import MODULE_TEST_TYPES


_PORTFOLIO_APPS = ('hub', 'generic', 'fintech', 'architect', 'leader', 'vibe')
_PORTFOLIO_PACKAGES = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')

ALL_MODULES: tuple[str, ...] = (
    'server',
    'devtools',
    *_PORTFOLIO_APPS,
    *(f'pkg-{p}' for p in _PORTFOLIO_PACKAGES),
    'feature',
)


def resolve_modules(flags: dict[str, Any]) -> list[str]:
    """Decide which modules to test based on flags.

    Precedence: explicit ``--module`` > inferred from ``--type``. With
    ``type=all`` we test every module that has any test type defined.
    """
    module = flags.get('module')
    test_type = flags.get('type', 'all')

    if module:
        return [module]

    if test_type == 'all':
        return [m for m in ALL_MODULES if MODULE_TEST_TYPES.get(m)]

    return [m for m in ALL_MODULES if test_type in MODULE_TEST_TYPES.get(m, [])]


def resolve_types_for_module(test_type: str, module: str) -> list[str]:
    """Expand 'all' into the concrete test types supported by ``module``."""
    if test_type == 'all':
        return list(MODULE_TEST_TYPES.get(module, []))
    return [test_type]
