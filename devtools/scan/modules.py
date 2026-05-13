"""Module definitions for project scanning.

Each module is a logical region of the project with specific rules for
file inclusión/exclusión. Modules are NOT necessarily 1:1 with directories —
they are code-defined profiles that map to scanning behavior.

Purpose-specific excludes allow different tools (conformance, formatter,
test, coverage) to have tailored file lists from the same module.

Portfolio monorepo structure:
  apps/{hub,generic,fintech,architect,leader,vibe}   — Astro 6 sites
  packages/{app-shared,content,cv-pdf,seo,ui}        — shared workspaces
  devtools/                                          — Python 3.14 CLI
  server/                                            — stub (no backend)
"""

from typing import Any


# Lista canonica de apps Astro del portfolio.
PORTFOLIO_APPS = ('hub', 'generic', 'fintech', 'architect', 'leader', 'vibe')

# Lista canonica de packages compartidos (workspace).
PORTFOLIO_PACKAGES = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')


def _astro_app_module(app_name: str) -> dict[str, Any]:
    """Genera la config de un module para una app Astro del monorepo."""
    return {
        'description': f'Astro 6 site (apps/{app_name})',
        'root': f'apps/{app_name}/',
        'extensions': ['ts', 'astro'],
        'exclude_patterns': [
            '**/node_modules/**',
            '**/.astro/**',
            '**/dist/**',
            '**/coverage/**',
        ],
        'purpose_excludes': {
            'test': [f'apps/{app_name}/tests/**'],
            'coverage': [
                f'apps/{app_name}/tests/**',
                f'apps/{app_name}/**/*.config.ts',
            ],
        },
        'docker': {
            'workdir': f'/app/apps/{app_name}',
            'strip_prefix': f'apps/{app_name}/',
        },
    }


def _package_module(pkg_name: str) -> dict[str, Any]:
    """Genera la config de un module para un package del monorepo."""
    return {
        'description': f'Shared workspace (packages/{pkg_name})',
        'root': f'packages/{pkg_name}/',
        'extensions': ['ts'],
        'exclude_patterns': [
            '**/node_modules/**',
            '**/dist/**',
            '**/coverage/**',
        ],
        'purpose_excludes': {
            'test': [f'packages/{pkg_name}/tests/**'],
            'coverage': [
                f'packages/{pkg_name}/tests/**',
                f'packages/{pkg_name}/**/*.config.ts',
            ],
        },
        'docker': {
            'workdir': f'/app/packages/{pkg_name}',
            'strip_prefix': f'packages/{pkg_name}/',
        },
    }


# ============================================================================
# MODULE DEFINITIONS
# ============================================================================

MODULES: dict[str, dict[str, Any]] = {
    # Server stub. NO existe backend en el portfolio; este module se mantiene
    # solo para que devtools/hooks/main.py (que verifica server/manage.py)
    # no falle. La deteccion de archivos retorna vacío porque no hay .py
    # de production en server/.
    'server': {
        'description': 'Stub placeholder (no backend in portfolio)',
        'root': 'server/',
        'extensions': ['py'],
        'ruff_config': None,
        'exclude_patterns': [
            '**/__pycache__/**',
            '**/*.pyc',
            # Excluimos manage.py — es solo stub
            'server/manage.py',
        ],
        'purpose_excludes': {
            'conformance': [],
            'formatter': [],
            'test': [],
            'coverage': [],
        },
        'docker': {
            'workdir': '/app/server',
            'strip_prefix': 'server/',
        },
    },
    'devtools': {
        'description': 'Development tools and CLI scripts (Python 3.14)',
        'root': 'devtools/',
        'extensions': ['py'],
        'ruff_config': 'devtools/ruff.toml',
        'exclude_patterns': [
            '**/__pycache__/**',
            '**/*.pyc',
        ],
        'purpose_excludes': {
            'conformance': [],
            'formatter': [],
        },
        'docker': {
            'workdir': '/app/devtools',
            'strip_prefix': 'devtools/',
        },
    },
}

# Inyectar dinámicamente las 6 apps Astro y los 5 packages.
for _app in PORTFOLIO_APPS:
    MODULES[_app] = _astro_app_module(_app)

for _pkg in PORTFOLIO_PACKAGES:
    MODULES[f'pkg-{_pkg}'] = _package_module(_pkg)


def get_module(name: str) -> dict[str, Any]:
    """Get module configuration by name.

    Parameters
    ----------
    name : str
        Module name (e.g. 'server', 'devtools', 'hub', 'generic', 'pkg-ui').

    Returns
    -------
    dict
        Module configuration.

    Raises
    ------
    ValueError
        If module name is not found.
    """
    if name not in MODULES:
        valid = ', '.join(sorted(MODULES.keys()))
        msg = f"Module '{name}' not found. Valid modules: {valid}"
        raise ValueError(msg)
    return MODULES[name]


def get_module_names() -> list[str]:
    """Return list of valid module names."""
    return sorted(MODULES.keys())


def get_purpose_excludes(module_name: str, purpose: str) -> list[str]:
    """Get purpose-specific exclude patterns for a module.

    Parameters
    ----------
    module_name : str
        Module name.
    purpose : str
        Tool purpose (conformance, formatter, test, coverage).

    Returns
    -------
    list[str]
        Additional exclude patterns for the purpose.
    """
    module = get_module(module_name)
    purpose_excludes = module.get('purpose_excludes', {})
    return purpose_excludes.get(purpose, [])


VALID_PURPOSES = ['conformance', 'formatter', 'test', 'coverage']
