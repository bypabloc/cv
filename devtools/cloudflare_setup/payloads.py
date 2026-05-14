"""
Cloudflare Pages payload builders.

Centralises the JSON shapes the Cloudflare REST API expects. Keeping these
in one place means the script and the docs only need to track one source of
truth for the project layout.
"""

from __future__ import annotations

from typing import Any

from devtools.cloudflare_setup.config import BUILD_COMMAND_TEMPLATE
from devtools.cloudflare_setup.config import COMMON_ENV_VARS
from devtools.cloudflare_setup.config import GITHUB_OWNER
from devtools.cloudflare_setup.config import GITHUB_REPO
from devtools.cloudflare_setup.config import PRODUCTION_BRANCH
from devtools.cloudflare_setup.config import AppConfig


def _env_vars(extra: dict[str, str] | None = None) -> dict[str, dict[str, str]]:
    """
    Convert flat ``{key: value}`` to Cloudflare's ``{key: {type, value}}`` shape.

    ``plain_text`` is the right type for non-secret build-time variables. Use
    ``secret_text`` for tokens (none here today, but documented for the future).
    """
    merged = dict(COMMON_ENV_VARS)
    if extra:
        merged.update(extra)
    return {k: {'type': 'plain_text', 'value': v} for k, v in merged.items()}


def build_create_project_payload(app: AppConfig) -> dict[str, Any]:
    """
    Compose the body for POST /accounts/{id}/pages/projects.

    Key fields explained:
      - ``build_config.root_dir``: where Cloudflare runs the build command.
        Empty string ('') means repo root, which is what pnpm workspaces need.
      - ``build_config.destination_dir``: where Astro emits the static site,
        relative to root_dir. For ``apps/generic/dist`` with root_dir=''.
      - ``deployment_configs.production.env_vars``: NODE_VERSION pins the
        toolchain; BASE_DOMAIN/BASE_SCHEME feed into our site-urls helper.
      - ``source.config.preview_deployment_setting=none``: avoid spawning a
        preview deploy for every PR branch (we'd pay 6x build credits).
    """
    build_command = BUILD_COMMAND_TEMPLATE.format(package_name=app.package_name)
    destination_dir = f'{app.root_dir}/dist'
    env_vars = _env_vars()

    return {
        'name': app.project_name,
        'production_branch': PRODUCTION_BRANCH,
        'source': {
            'type': 'github',
            'config': {
                'owner': GITHUB_OWNER,
                'repo_name': GITHUB_REPO,
                'production_branch': PRODUCTION_BRANCH,
                'deployments_enabled': True,
                'pr_comments_enabled': False,
                'production_deployments_enabled': True,
                # 'none' = only build production branch on push, no preview
                # noise per PR. Switch to 'all' if you want PR previews later.
                'preview_deployment_setting': 'none',
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


def build_patch_project_payload(app: AppConfig) -> dict[str, Any]:
    """
    Body for PATCH on an existing project — keeps build_config and env_vars
    aligned with the canonical config without recreating the project.
    """
    build_command = BUILD_COMMAND_TEMPLATE.format(package_name=app.package_name)
    destination_dir = f'{app.root_dir}/dist'
    env_vars = _env_vars()

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
