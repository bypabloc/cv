"""
Configuration for the portfolio Cloudflare Pages setup.

Six apps and three environments (dev | stage | prod) -> 18 Pages projects.
Project name and custom domain are derived from (app, env):

  prod   generic -> name `generic`,        domain `the-full-stack.com` (apex)
  prod   <niche> -> name `<niche>`,        domain `<niche>.portfolio.the-full-stack.com`
  dev    generic -> name `generic-dev`,    domain `portfolio.dev.the-full-stack.com`
  dev    <niche> -> name `<niche>-dev`,    domain `<niche>.portfolio.dev.the-full-stack.com`
  stage  generic -> name `generic-stage`,  domain `portfolio.stage.the-full-stack.com`
  stage  <niche> -> name `<niche>-stage`,  domain `<niche>.portfolio.stage.the-full-stack.com`

Reading order:
  1. APPS  — niche-level config (package_name, root_dir) common to all envs.
  2. ENVS  — env-level overrides (branch, base_domain, apex_domain, api,
             Turnstile sitekey).
  3. Helpers (project_name_for, custom_domain_for, site_url_for) — derive
     the per-(app, env) values from APPS + ENVS.
  4. BUILD_COMMAND_TEMPLATE / GLOBAL_ENV_VARS — invariant across envs.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """One Astro app inside the monorepo (niche-level, env-agnostic)."""

    project_name: (
        str  # niche slug (also Pages project name in prod, e.g. 'generic')
    )
    package_name: str  # pnpm package name for --filter
    root_dir: str  # path relative to repo root (where the Astro app lives)


@dataclass(frozen=True)
class EnvConfig:
    """One deployment environment (dev | stage | prod)."""

    env: str  # 'dev' | 'stage' | 'prod'
    branch: str  # GitHub branch that Pages builds: 'main' | 'dev' | 'stage'
    base_domain: (
        str  # FQDN the niches attach to (e.g. 'portfolio.the-full-stack.com')
    )
    apex_domain: (
        str | None
    )  # only set in prod; generic falls back to apex when present
    api_endpoint: str  # https://api.<base_domain>
    turnstile_sitekey: str  # 1 Cloudflare Turnstile widget per env


# the-full-stack.com is the apex; generic is the canonical apex app in prod.
APEX_DOMAIN = 'the-full-stack.com'


APPS: tuple[AppConfig, ...] = (
    AppConfig(
        project_name='generic',
        package_name='@portfolio/generic',
        root_dir='apps/generic',
    ),
    AppConfig(
        project_name='hub',
        package_name='@portfolio/hub',
        root_dir='apps/hub',
    ),
    AppConfig(
        project_name='fintech',
        package_name='@portfolio/fintech',
        root_dir='apps/fintech',
    ),
    AppConfig(
        project_name='architect',
        package_name='@portfolio/architect',
        root_dir='apps/architect',
    ),
    AppConfig(
        project_name='leader',
        package_name='@portfolio/leader',
        root_dir='apps/leader',
    ),
    AppConfig(
        project_name='vibe',
        package_name='@portfolio/vibe',
        root_dir='apps/vibe',
    ),
)


# Per-environment configuration. PUBLIC_TURNSTILE_SITEKEY is publica
# (no es secreto): la verificacion server-side va con TURNSTILE_SECRET_KEY
# en SSM (ver .claude/rules/serverless-secrets.md).
ENVS: dict[str, EnvConfig] = {
    'prod': EnvConfig(
        env='prod',
        branch='main',
        base_domain=f'portfolio.{APEX_DOMAIN}',
        apex_domain=APEX_DOMAIN,
        api_endpoint=f'https://api.portfolio.{APEX_DOMAIN}',
        turnstile_sitekey='0x4AAAAAADPSoiQA_-LcRafo',
    ),
    'dev': EnvConfig(
        env='dev',
        branch='dev',
        base_domain=f'portfolio.dev.{APEX_DOMAIN}',
        apex_domain=None,
        api_endpoint=f'https://api.portfolio.dev.{APEX_DOMAIN}',
        turnstile_sitekey='0x4AAAAAADQjTYp6s1o66YDV',
    ),
    'stage': EnvConfig(
        env='stage',
        branch='stage',
        base_domain=f'portfolio.stage.{APEX_DOMAIN}',
        apex_domain=None,
        api_endpoint=f'https://api.portfolio.stage.{APEX_DOMAIN}',
        turnstile_sitekey='0x4AAAAAADQjTq8AtQXbm3Oq',
    ),
}

VALID_ENVS: tuple[str, ...] = tuple(ENVS.keys())


# ---- Derived (per-(app, env)) values --------------------------------------


def project_name_for(app: AppConfig, env: str) -> str:
    """Pages project name. prod: 'generic'; dev/stage: 'generic-dev'/'generic-stage'."""
    if env == 'prod':
        return app.project_name
    return f'{app.project_name}-{env}'


def custom_domain_for(app: AppConfig, env_cfg: EnvConfig) -> str:
    """
    FQDN attached to the project.

    - prod   generic -> the-full-stack.com (apex)
    - prod   <niche> -> <niche>.portfolio.the-full-stack.com
    - dev    generic -> portfolio.dev.the-full-stack.com (no apex in dev/stage)
    - dev    <niche> -> <niche>.portfolio.dev.the-full-stack.com
    - stage  analog.
    """
    if app.project_name == 'generic':
        return env_cfg.apex_domain or env_cfg.base_domain
    return f'{app.project_name}.{env_cfg.base_domain}'


def site_url_for(app: AppConfig, env_cfg: EnvConfig) -> str:
    """https://<custom_domain>."""
    return f'https://{custom_domain_for(app, env_cfg)}'


# ---- Build invariants -----------------------------------------------------


# Build runs from the repo root so pnpm workspaces can resolve internal deps.
# `--filter @portfolio/<app>...` (three dots) builds the app + all internal
# workspace deps it needs (content, ui, seo, cv-pdf, app-shared, cv-filters).
BUILD_COMMAND_TEMPLATE = (
    'pnpm install --frozen-lockfile && pnpm --filter {package_name}... build'
)


# Truly global env vars (same value across every env). Per-env vars
# (BASE_DOMAIN, APEX_DOMAIN, PUBLIC_API_ENDPOINT, PUBLIC_TURNSTILE_SITEKEY,
# SITE_URL) are derived per-(app, env_cfg) in payloads._env_vars().
GLOBAL_ENV_VARS: dict[str, str] = {
    'NODE_VERSION': '24',
    'PNPM_VERSION': '11.0.9',
    'BASE_SCHEME': 'https',
}


GITHUB_OWNER = 'bypabloc'
GITHUB_REPO = 'cv'
