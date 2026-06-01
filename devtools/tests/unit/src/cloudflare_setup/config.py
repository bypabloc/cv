"""Unit tests for cloudflare_setup.config.

Path mirroring: devtools/cloudflare_setup/config.py -> this file.

Cubre:
- ENVS declara dev/stage/prod con los valores correctos
- project_name_for aplica sufijo -dev/-stage y deja prod sin sufijo
- custom_domain_for arma el FQDN segun env+niche (generic vs niches)
- site_url_for produce https://<custom_domain>
"""

import pytest

from cloudflare_setup.config import APEX_DOMAIN
from cloudflare_setup.config import APPS
from cloudflare_setup.config import ENVS
from cloudflare_setup.config import VALID_ENVS
from cloudflare_setup.config import AppConfig
from cloudflare_setup.config import EnvConfig
from cloudflare_setup.config import custom_domain_for
from cloudflare_setup.config import project_name_for
from cloudflare_setup.config import site_url_for


pytestmark = pytest.mark.unit


# ---- ENVS ----------------------------------------------------------------


class TestEnvsRegistry:
    """ENVS declara los 3 entornos con los valores reales de Cloudflare."""

    def test_valid_envs_are_dev_stage_prod(self):
        assert set(VALID_ENVS) == {'dev', 'stage', 'prod'}

    def test_prod_has_apex_domain_set(self):
        cfg = ENVS['prod']
        assert cfg.branch == 'main'
        assert cfg.base_domain == f'portfolio.{APEX_DOMAIN}'
        assert cfg.apex_domain == APEX_DOMAIN
        assert cfg.api_endpoint == f'https://api.portfolio.{APEX_DOMAIN}'

    def test_dev_has_no_apex_domain(self):
        cfg = ENVS['dev']
        assert cfg.branch == 'dev'
        assert cfg.base_domain == f'portfolio.dev.{APEX_DOMAIN}'
        assert cfg.apex_domain is None
        assert cfg.api_endpoint == f'https://api.portfolio.dev.{APEX_DOMAIN}'

    def test_stage_has_no_apex_domain(self):
        cfg = ENVS['stage']
        assert cfg.branch == 'stage'
        assert cfg.base_domain == f'portfolio.stage.{APEX_DOMAIN}'
        assert cfg.apex_domain is None
        assert cfg.api_endpoint == f'https://api.portfolio.stage.{APEX_DOMAIN}'

    def test_each_env_has_distinct_turnstile_sitekey(self):
        sitekeys = {ENVS[e].turnstile_sitekey for e in ('prod', 'dev', 'stage')}
        assert len(sitekeys) == 3


# ---- project_name_for ----------------------------------------------------


class TestProjectNameFor:
    """Sufijo -<env> en dev/stage; prod sin sufijo."""

    @pytest.fixture
    def app_generic(self):
        return AppConfig(
            project_name='generic',
            package_name='@portfolio/generic',
            root_dir='apps/generic',
        )

    @pytest.fixture
    def app_hub(self):
        return AppConfig(
            project_name='hub',
            package_name='@portfolio/hub',
            root_dir='apps/hub',
        )

    def test_prod_generic_has_no_suffix(self, app_generic):
        assert project_name_for(app_generic, 'prod') == 'generic'

    def test_prod_niche_has_no_suffix(self, app_hub):
        assert project_name_for(app_hub, 'prod') == 'hub'

    def test_dev_generic_gets_dev_suffix(self, app_generic):
        assert project_name_for(app_generic, 'dev') == 'generic-dev'

    def test_dev_niche_gets_dev_suffix(self, app_hub):
        assert project_name_for(app_hub, 'dev') == 'hub-dev'

    def test_stage_generic_gets_stage_suffix(self, app_generic):
        assert project_name_for(app_generic, 'stage') == 'generic-stage'

    def test_stage_niche_gets_stage_suffix(self, app_hub):
        assert project_name_for(app_hub, 'stage') == 'hub-stage'


# ---- custom_domain_for ---------------------------------------------------


class TestCustomDomainFor:
    """
    prod   generic -> apex (the-full-stack.com)
    prod   niche   -> niche.portfolio.the-full-stack.com
    dev/st generic -> portfolio.<env>.the-full-stack.com (base_domain)
    dev/st niche   -> niche.portfolio.<env>.the-full-stack.com
    """

    @pytest.fixture
    def app_generic(self):
        return AppConfig(
            project_name='generic',
            package_name='@portfolio/generic',
            root_dir='apps/generic',
        )

    @pytest.fixture
    def app_hub(self):
        return AppConfig(
            project_name='hub',
            package_name='@portfolio/hub',
            root_dir='apps/hub',
        )

    def test_prod_generic_uses_apex(self, app_generic):
        result = custom_domain_for(app_generic, ENVS['prod'])
        assert result == 'the-full-stack.com'

    def test_prod_niche_uses_portfolio_subdomain(self, app_hub):
        result = custom_domain_for(app_hub, ENVS['prod'])
        assert result == 'hub.portfolio.the-full-stack.com'

    def test_dev_generic_uses_base_domain(self, app_generic):
        result = custom_domain_for(app_generic, ENVS['dev'])
        assert result == 'portfolio.dev.the-full-stack.com'

    def test_dev_niche_uses_env_subdomain(self, app_hub):
        result = custom_domain_for(app_hub, ENVS['dev'])
        assert result == 'hub.portfolio.dev.the-full-stack.com'

    def test_stage_generic_uses_base_domain(self, app_generic):
        result = custom_domain_for(app_generic, ENVS['stage'])
        assert result == 'portfolio.stage.the-full-stack.com'

    def test_stage_niche_uses_env_subdomain(self, app_hub):
        result = custom_domain_for(app_hub, ENVS['stage'])
        assert result == 'hub.portfolio.stage.the-full-stack.com'


# ---- site_url_for --------------------------------------------------------


class TestSiteUrlFor:
    """site_url_for = https + custom_domain_for."""

    def test_prod_generic_returns_apex_https(self):
        app = APPS[0]  # generic
        assert site_url_for(app, ENVS['prod']) == 'https://the-full-stack.com'

    def test_dev_hub_returns_env_subdomain_https(self):
        hub = next(a for a in APPS if a.project_name == 'hub')
        assert (
            site_url_for(hub, ENVS['dev'])
            == 'https://hub.portfolio.dev.the-full-stack.com'
        )


# ---- APPS ---------------------------------------------------------------


def test_apps_has_seven_entries_six_niches_plus_admin():
    names = {a.project_name for a in APPS}
    assert names == {
        'generic',
        'hub',
        'fintech',
        'architect',
        'leader',
        'vibe',
        'admin',
    }


def test_apps_carries_app_type_and_build_output_dir_fields():
    """AppConfig es env-agnostic + lleva app_type/build_output_dir."""
    fields = set(AppConfig.__dataclass_fields__)
    assert fields == {
        'project_name',
        'package_name',
        'root_dir',
        'app_type',
        'build_output_dir',
    }


def test_six_astro_apps_default_to_astro_dist():
    """Las 6 apps Astro preservan los defaults app_type/build_output_dir."""
    astro = [a for a in APPS if a.project_name != 'admin']
    assert [a.app_type for a in astro] == ['astro'] * 6
    assert [a.build_output_dir for a in astro] == ['dist'] * 6


def test_admin_app_is_nextjs_with_out_output_dir():
    admin = next(a for a in APPS if a.project_name == 'admin')
    assert admin.package_name == '@portfolio/admin'
    assert admin.root_dir == 'admin'
    assert admin.app_type == 'nextjs'
    assert admin.build_output_dir == 'out'


def test_admin_project_name_gets_env_suffix():
    admin = next(a for a in APPS if a.project_name == 'admin')
    assert project_name_for(admin, 'prod') == 'admin'
    assert project_name_for(admin, 'dev') == 'admin-dev'
    assert project_name_for(admin, 'stage') == 'admin-stage'


def test_admin_custom_domain_is_not_apex_in_prod():
    """admin NO es apex (a diferencia de generic): admin.portfolio.<base>."""
    admin = next(a for a in APPS if a.project_name == 'admin')
    assert (
        custom_domain_for(admin, ENVS['prod'])
        == 'admin.portfolio.the-full-stack.com'
    )
    assert (
        custom_domain_for(admin, ENVS['dev'])
        == 'admin.portfolio.dev.the-full-stack.com'
    )
    assert (
        custom_domain_for(admin, ENVS['stage'])
        == 'admin.portfolio.stage.the-full-stack.com'
    )


def test_env_config_carries_branch_and_domains():
    fields = set(EnvConfig.__dataclass_fields__)
    assert fields == {
        'env',
        'branch',
        'base_domain',
        'apex_domain',
        'api_endpoint',
        'turnstile_sitekey',
    }
