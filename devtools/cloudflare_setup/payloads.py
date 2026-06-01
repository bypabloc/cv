"""
Cloudflare Pages payload builders.

Centralises the JSON shapes the Cloudflare REST API expects. Each payload
is parameterised by (app, env_cfg) so the same shape works for every
(niche x env) combination.
"""

from __future__ import annotations

from typing import Any

from devtools.cloudflare_setup.config import BUILD_COMMAND_TEMPLATE
from devtools.cloudflare_setup.config import GITHUB_OWNER
from devtools.cloudflare_setup.config import GITHUB_REPO
from devtools.cloudflare_setup.config import GLOBAL_ENV_VARS
from devtools.cloudflare_setup.config import AppConfig
from devtools.cloudflare_setup.config import EnvConfig
from devtools.cloudflare_setup.config import custom_domain_for
from devtools.cloudflare_setup.config import project_name_for
from devtools.cloudflare_setup.config import site_url_for


def _env_vars(app: AppConfig, env_cfg: EnvConfig) -> dict[str, dict[str, str]]:
    """
    Build the per-(app, env) env_vars dict in Cloudflare's
    ``{key: {type, value}}`` shape.

    ``plain_text`` is the right type for non-secret build-time variables.
    Use ``secret_text`` for tokens (none here today — Turnstile secret
    lives in SSM, not in Pages env vars).

    Las apps Astro consumen ``PUBLIC_*``; el admin Next.js consume
    ``NEXT_PUBLIC_*`` (Next inlinea ese prefijo en el bundle del browser).
    Las globales (BASE_*, APEX_DOMAIN, NODE/PNPM_VERSION) se mantienen
    para ambos toolchains.
    """
    merged: dict[str, str] = dict(GLOBAL_ENV_VARS)
    merged.update(
        {
            'BASE_DOMAIN': env_cfg.base_domain,
            'PUBLIC_API_ENDPOINT': env_cfg.api_endpoint,
            'PUBLIC_TURNSTILE_SITEKEY': env_cfg.turnstile_sitekey,
            'SITE_URL': site_url_for(app, env_cfg),
        }
    )
    if env_cfg.apex_domain is not None:
        merged['APEX_DOMAIN'] = env_cfg.apex_domain
    if app.app_type == 'nextjs':
        # NEXT_PUBLIC_WEBAUTHN_RP_ID = el hostname (sin esquema), por env.
        # NEXT_PUBLIC_ADMIN_URL = https://<hostname> (self URL del admin).
        merged.update(
            {
                'NEXT_PUBLIC_API_ENDPOINT': env_cfg.api_endpoint,
                'NEXT_PUBLIC_TURNSTILE_SITEKEY': env_cfg.turnstile_sitekey,
                'NEXT_PUBLIC_ADMIN_URL': site_url_for(app, env_cfg),
                'NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS': '30000',
                'NEXT_PUBLIC_WEBAUTHN_RP_ID': custom_domain_for(app, env_cfg),
                'NEXT_PUBLIC_FEATURE_MFA': 'true',
            }
        )
    return {k: {'type': 'plain_text', 'value': v} for k, v in merged.items()}


def build_create_project_payload(
    app: AppConfig, env_cfg: EnvConfig
) -> dict[str, Any]:
    """
    Compose the body for POST /accounts/{id}/pages/projects.

    Key fields explained:
      - ``build_config.root_dir``: where Cloudflare runs the build command.
        Empty string ('') means repo root, which is what pnpm workspaces need.
      - ``build_config.destination_dir``: where the toolchain emits the
        static site, relative to root_dir. Astro -> ``<root>/dist``
        (ej. ``apps/generic/dist``), Next.js export -> ``<root>/out``
        (ej. ``admin/out``). Derivado de ``app.build_output_dir``.
      - ``deployment_configs.production.env_vars``: derived per env from
        env_cfg + app (see ``_env_vars``).
      - ``source.config.preview_deployment_setting=none`` +
        ``preview_branch_includes=[env_cfg.branch]`` +
        ``preview_branch_excludes=['*']``: avoid building every branch that
        lands in the repo. Each Pages project builds ONLY its own branch.
    """
    build_command = BUILD_COMMAND_TEMPLATE.format(package_name=app.package_name)
    destination_dir = f'{app.root_dir}/{app.build_output_dir}'
    env_vars = _env_vars(app, env_cfg)

    return {
        'name': project_name_for(app, env_cfg.env),
        'production_branch': env_cfg.branch,
        'source': {
            'type': 'github',
            'config': {
                'owner': GITHUB_OWNER,
                'repo_name': GITHUB_REPO,
                'production_branch': env_cfg.branch,
                'deployments_enabled': True,
                'pr_comments_enabled': False,
                'production_deployments_enabled': True,
                # 'none' = only build production branch on push, no preview
                # noise per PR. preview_branch_includes/excludes lock the
                # project to a single branch so PRs to other branches do
                # not trigger builds in the wrong env (see
                # memory `cloudflare-pages-preview-branch-fix`).
                'preview_deployment_setting': 'none',
                'preview_branch_includes': [env_cfg.branch],
                'preview_branch_excludes': ['*'],
            },
        },
        'build_config': {
            'build_command': build_command,
            'destination_dir': destination_dir,
            'root_dir': '',
        },
        'deployment_configs': {
            'production': {'env_vars': env_vars},
            'preview': {'env_vars': env_vars},
        },
    }


def build_patch_project_payload(
    app: AppConfig, env_cfg: EnvConfig
) -> dict[str, Any]:
    """
    Body for PATCH on an existing project. Keeps build_config and env_vars
    aligned with config.py (config-as-source-of-truth: re-running the
    script reverts manual changes done in the Cloudflare dashboard).
    """
    build_command = BUILD_COMMAND_TEMPLATE.format(package_name=app.package_name)
    destination_dir = f'{app.root_dir}/{app.build_output_dir}'
    env_vars = _env_vars(app, env_cfg)

    return {
        'build_config': {
            'build_command': build_command,
            'destination_dir': destination_dir,
            'root_dir': '',
        },
        'deployment_configs': {
            'production': {'env_vars': env_vars},
            'preview': {'env_vars': env_vars},
        },
    }
