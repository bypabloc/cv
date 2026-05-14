"""
Configuration for the portfolio Cloudflare Pages setup.

Six apps, one Pages project per app. The apex domain points to `generic`;
the other five apps map 1:1 to subdomains under `the-full-stack.com`.

Reading order:
  1. APPS — single source of truth for project_name <-> root_dir <-> domain.
  2. BUILD_COMMAND_TEMPLATE — same shape for every app, only the pnpm filter changes.
  3. COMMON_ENV_VARS — shared between production and preview.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """One Astro app inside the monorepo."""

    project_name: str  # Pages project name (also the *.pages.dev subdomain)
    package_name: str  # pnpm package name for --filter
    root_dir: str  # path relative to repo root (where the Astro app lives)
    custom_domain: str  # apex or subdomain to associate via Pages domains API


# the-full-stack.com is the apex; generic is the canonical apex app.
APEX_DOMAIN = 'the-full-stack.com'

APPS: tuple[AppConfig, ...] = (
    AppConfig(
        project_name='generic',
        package_name='@portfolio/generic',
        root_dir='apps/generic',
        custom_domain=APEX_DOMAIN,
    ),
    AppConfig(
        project_name='hub',
        package_name='@portfolio/hub',
        root_dir='apps/hub',
        custom_domain=f'hub.{APEX_DOMAIN}',
    ),
    AppConfig(
        project_name='fintech',
        package_name='@portfolio/fintech',
        root_dir='apps/fintech',
        custom_domain=f'fintech.{APEX_DOMAIN}',
    ),
    AppConfig(
        project_name='architect',
        package_name='@portfolio/architect',
        root_dir='apps/architect',
        custom_domain=f'architect.{APEX_DOMAIN}',
    ),
    AppConfig(
        project_name='leader',
        package_name='@portfolio/leader',
        root_dir='apps/leader',
        custom_domain=f'leader.{APEX_DOMAIN}',
    ),
    AppConfig(
        project_name='vibe',
        package_name='@portfolio/vibe',
        root_dir='apps/vibe',
        custom_domain=f'vibe.{APEX_DOMAIN}',
    ),
)


# Build runs from the repo root so pnpm workspaces can resolve internal deps.
# `--filter @portfolio/<app>...` (three dots) builds the app + all internal
# workspace deps it needs (content, ui, seo, cv-pdf, app-shared, cv-filters).
BUILD_COMMAND_TEMPLATE = (
    'pnpm install --frozen-lockfile && pnpm --filter {package_name}... build'
)


# These flow into both production and preview deployment configs.
# NODE_VERSION/PNPM_VERSION pin the toolchain to match the local repo
# (Cloudflare's default is Node 20, our package.json#engines wants 24).
COMMON_ENV_VARS: dict[str, str] = {
    'NODE_VERSION': '24',
    'PNPM_VERSION': '11.0.9',
    'BASE_DOMAIN': APEX_DOMAIN,
    'BASE_SCHEME': 'https',
}


GITHUB_OWNER = 'bypabloc'
GITHUB_REPO = 'cv'
PRODUCTION_BRANCH = 'main'
