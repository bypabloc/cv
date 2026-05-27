"""Unit tests for cloudflare_setup.payloads.

Path mirroring: devtools/cloudflare_setup/payloads.py -> this file.

Cubre:
- build_create_project_payload: name, branch, env_vars derivados, preview_branch_includes
- build_patch_project_payload: actualiza build_config y env_vars (config-as-truth)
- _env_vars: incluye APEX_DOMAIN solo en prod
"""

import pytest

from cloudflare_setup.config import APPS
from cloudflare_setup.config import ENVS
from cloudflare_setup.config import AppConfig
from cloudflare_setup.payloads import _env_vars
from cloudflare_setup.payloads import build_create_project_payload
from cloudflare_setup.payloads import build_patch_project_payload


pytestmark = pytest.mark.unit


@pytest.fixture
def hub():
    return next(a for a in APPS if a.project_name == 'hub')


@pytest.fixture
def generic():
    return next(a for a in APPS if a.project_name == 'generic')


# ---- _env_vars ----------------------------------------------------------


class TestEnvVarsProd:
    """Prod incluye APEX_DOMAIN; los demas valores derivan de env_cfg + app."""

    def test_prod_includes_apex_domain(self, hub):
        result = _env_vars(hub, ENVS['prod'])
        assert result['APEX_DOMAIN'] == {
            'type': 'plain_text',
            'value': 'the-full-stack.com',
        }

    def test_prod_base_domain_is_portfolio_subdomain(self, hub):
        result = _env_vars(hub, ENVS['prod'])
        assert result['BASE_DOMAIN']['value'] == 'portfolio.the-full-stack.com'

    def test_prod_hub_site_url_uses_niche_subdomain(self, hub):
        result = _env_vars(hub, ENVS['prod'])
        assert (
            result['SITE_URL']['value']
            == 'https://hub.portfolio.the-full-stack.com'
        )

    def test_prod_generic_site_url_is_apex(self, generic):
        result = _env_vars(generic, ENVS['prod'])
        assert result['SITE_URL']['value'] == 'https://the-full-stack.com'

    def test_global_env_vars_carry_node_pnpm_scheme(self, hub):
        result = _env_vars(hub, ENVS['prod'])
        assert result['NODE_VERSION']['value'] == '24'
        assert result['PNPM_VERSION']['value'] == '11.0.9'
        assert result['BASE_SCHEME']['value'] == 'https'


class TestEnvVarsDev:
    """Dev no incluye APEX_DOMAIN; site_url usa base_domain para generic."""

    def test_dev_does_not_include_apex_domain(self, hub):
        result = _env_vars(hub, ENVS['dev'])
        assert 'APEX_DOMAIN' not in result

    def test_dev_base_domain_has_env_segment(self, hub):
        result = _env_vars(hub, ENVS['dev'])
        assert (
            result['BASE_DOMAIN']['value'] == 'portfolio.dev.the-full-stack.com'
        )

    def test_dev_api_endpoint_has_env_segment(self, hub):
        result = _env_vars(hub, ENVS['dev'])
        assert (
            result['PUBLIC_API_ENDPOINT']['value']
            == 'https://api.portfolio.dev.the-full-stack.com'
        )

    def test_dev_hub_site_url(self, hub):
        result = _env_vars(hub, ENVS['dev'])
        assert (
            result['SITE_URL']['value']
            == 'https://hub.portfolio.dev.the-full-stack.com'
        )

    def test_dev_generic_site_url_uses_base_domain(self, generic):
        result = _env_vars(generic, ENVS['dev'])
        assert (
            result['SITE_URL']['value']
            == 'https://portfolio.dev.the-full-stack.com'
        )

    def test_dev_turnstile_sitekey_differs_from_prod(self, hub):
        dev_key = _env_vars(hub, ENVS['dev'])['PUBLIC_TURNSTILE_SITEKEY'][
            'value'
        ]
        prod_key = _env_vars(hub, ENVS['prod'])['PUBLIC_TURNSTILE_SITEKEY'][
            'value'
        ]
        assert dev_key != prod_key


class TestEnvVarsStage:
    """Stage analog a dev pero con .stage. en lugar de .dev."""

    def test_stage_base_domain(self, hub):
        result = _env_vars(hub, ENVS['stage'])
        assert (
            result['BASE_DOMAIN']['value']
            == 'portfolio.stage.the-full-stack.com'
        )

    def test_stage_does_not_include_apex_domain(self, hub):
        result = _env_vars(hub, ENVS['stage'])
        assert 'APEX_DOMAIN' not in result


# ---- build_create_project_payload --------------------------------------


class TestCreatePayload:
    """Payload de POST /pages/projects: name, branch, env_vars, preview."""

    def test_prod_hub_name_has_no_suffix(self, hub):
        payload = build_create_project_payload(hub, ENVS['prod'])
        assert payload['name'] == 'hub'

    def test_dev_hub_name_has_dev_suffix(self, hub):
        payload = build_create_project_payload(hub, ENVS['dev'])
        assert payload['name'] == 'hub-dev'

    def test_dev_production_branch_is_dev(self, hub):
        payload = build_create_project_payload(hub, ENVS['dev'])
        assert payload['production_branch'] == 'dev'
        assert payload['source']['config']['production_branch'] == 'dev'

    def test_stage_production_branch_is_stage(self, hub):
        payload = build_create_project_payload(hub, ENVS['stage'])
        assert payload['production_branch'] == 'stage'

    def test_prod_production_branch_is_main(self, hub):
        payload = build_create_project_payload(hub, ENVS['prod'])
        assert payload['production_branch'] == 'main'

    def test_preview_branches_locked_to_own_branch(self, hub):
        """Cada project Pages solo construye su propia branch."""
        payload = build_create_project_payload(hub, ENVS['dev'])
        cfg = payload['source']['config']
        assert cfg['preview_branch_includes'] == ['dev']
        assert cfg['preview_branch_excludes'] == ['*']
        assert cfg['preview_deployment_setting'] == 'none'

    def test_build_command_targets_app_package(self, hub):
        payload = build_create_project_payload(hub, ENVS['prod'])
        assert '@portfolio/hub...' in payload['build_config']['build_command']

    def test_destination_dir_is_app_dist(self, hub):
        payload = build_create_project_payload(hub, ENVS['prod'])
        assert payload['build_config']['destination_dir'] == 'apps/hub/dist'

    def test_root_dir_is_repo_root(self, hub):
        payload = build_create_project_payload(hub, ENVS['prod'])
        assert payload['build_config']['root_dir'] == ''

    def test_env_vars_applied_to_production_and_preview(self, hub):
        payload = build_create_project_payload(hub, ENVS['prod'])
        prod_vars = payload['deployment_configs']['production']['env_vars']
        preview_vars = payload['deployment_configs']['preview']['env_vars']
        assert prod_vars == preview_vars  # same shape
        assert (
            prod_vars['BASE_DOMAIN']['value'] == 'portfolio.the-full-stack.com'
        )


# ---- build_patch_project_payload ---------------------------------------


class TestPatchPayload:
    """Patch payload: actualiza build_config + env_vars (config-as-truth)."""

    def test_patch_includes_build_config(self, hub):
        payload = build_patch_project_payload(hub, ENVS['dev'])
        assert payload['build_config']['destination_dir'] == 'apps/hub/dist'

    def test_patch_includes_env_vars_per_env(self, hub):
        payload = build_patch_project_payload(hub, ENVS['dev'])
        prod_vars = payload['deployment_configs']['production']['env_vars']
        assert (
            prod_vars['BASE_DOMAIN']['value']
            == 'portfolio.dev.the-full-stack.com'
        )
        assert 'APEX_DOMAIN' not in prod_vars

    def test_patch_does_not_include_name_or_branch(self, hub):
        """Esos campos son inmutables tras crear; el patch no los lleva."""
        payload = build_patch_project_payload(hub, ENVS['dev'])
        assert 'name' not in payload
        assert 'production_branch' not in payload
        assert 'source' not in payload
