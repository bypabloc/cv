"""Filesystem paths shared by devtools scripts.

Single source of truth for project root, docker directory, etc. Avoids
hardcoding ``Path(__file__).resolve().parent.parent.parent`` in every
module and keeps the relationships explicit.

Portfolio monorepo:
    - PROJECT_ROOT/apps/<APP>      (6 Astro sites)
    - PROJECT_ROOT/packages/<PKG>  (5 shared workspaces)
    - PROJECT_ROOT/server          (stub placeholder, no backend)
    - PROJECT_ROOT/tests/feature   (Playwright E2E shared)
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
DEVTOOLS_DIR: Path = PROJECT_ROOT / 'devtools'
DOCKER_DIR: Path = PROJECT_ROOT / 'docker'
SERVER_DIR: Path = PROJECT_ROOT / 'server'

APPS_DIR: Path = PROJECT_ROOT / 'apps'
PACKAGES_DIR: Path = PROJECT_ROOT / 'packages'

# Apps Astro disponibles en el portfolio.
PORTFOLIO_APPS: tuple[str, ...] = (
    'hub',
    'generic',
    'fintech',
    'architect',
    'leader',
    'vibe',
)

# Packages compartidos en el portfolio.
PORTFOLIO_PACKAGES: tuple[str, ...] = (
    'app-shared',
    'content',
    'cv-pdf',
    'seo',
    'ui',
)

# Test E2E shared (Playwright) — root-level, no por-app.
FEATURE_TESTS_DIR: Path = PROJECT_ROOT / 'tests' / 'feature'

# Aliases legacy: muchos modulos del fuente referencian DASHBOARD_DIR /
# LANDING_DIR. Los mantenemos como punteros al primer app del portfolio
# para que imports antiguos no exploten, pero NO se usan en logica nueva.
DASHBOARD_DIR: Path = APPS_DIR / 'generic'  # legacy alias
LANDING_DIR: Path = APPS_DIR / 'generic'  # legacy alias
E2E_DIR: Path = FEATURE_TESTS_DIR  # legacy alias
