"""Unit tests para common.config (Settings)."""

from __future__ import annotations

import pytest

from common.config import Settings, get_settings

pytestmark = pytest.mark.unit


class TestSettings:
    """Settings carga env vars con typed validation."""

    def test_when_no_env_then_uses_defaults(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given sin env vars seteadas (solo defaults),
        When Settings(),
        Then todos los fields tienen los defaults documentados.
        """
        # Limpiar env vars que afecten Settings
        for var in [
            'STAGE',
            'LOG_LEVEL',
            'CONTACTS_TABLE_NAME',
            'TRACKING_TABLE_NAME',
            'CACHE_TABLE_NAME',
        ]:
            monkeypatch.delenv(var, raising=False)

        get_settings.cache_clear()
        s = Settings()

        assert s.stage == 'dev'
        assert s.aws_region == 'us-east-1'
        assert s.log_level == 'INFO'
        assert s.contacts_table_name == 'portfolio-contacts-dev'
        assert s.tracking_table_name == 'portfolio-tracking-dev'
        assert s.cache_table_name == 'portfolio-cache-dev'
        assert s.kms_key_alias == 'alias/portfolio-lambdas'

    def test_when_env_set_then_overrides_defaults(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given env vars seteadas,
        When Settings(),
        Then overrides defaults.
        """
        monkeypatch.setenv('STAGE', 'prod')
        monkeypatch.setenv('LOG_LEVEL', 'WARNING')
        monkeypatch.setenv('CONTACTS_TABLE_NAME', 'portfolio-contacts-prod')

        get_settings.cache_clear()
        s = Settings()

        assert s.stage == 'prod'
        assert s.log_level == 'WARNING'
        assert s.contacts_table_name == 'portfolio-contacts-prod'

    def test_is_prod_helper(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given STAGE=prod,
        When settings.is_prod,
        Then True.
        """
        monkeypatch.setenv('STAGE', 'prod')
        get_settings.cache_clear()
        s = Settings()

        assert s.is_prod is True
        assert s.is_dev is False

    def test_is_dev_helper(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given STAGE=dev, When settings.is_dev, Then True."""
        monkeypatch.setenv('STAGE', 'dev')
        get_settings.cache_clear()
        s = Settings()

        assert s.is_dev is True
        assert s.is_prod is False

    def test_is_stage_helper(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given STAGE=stage,
        When settings.is_stage,
        Then True y is_dev/is_prod son False.
        """
        monkeypatch.setenv('STAGE', 'stage')
        get_settings.cache_clear()
        s = Settings()

        assert s.is_stage is True
        assert s.is_dev is False
        assert s.is_prod is False


class TestGetSettingsCache:
    """get_settings - singleton LRU cache."""

    def test_when_called_twice_then_same_instance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given get_settings() llamado 2 veces,
        When,
        Then retorna misma instancia (LRU cache).
        """
        monkeypatch.setenv('STAGE', 'dev')
        get_settings.cache_clear()

        s1 = get_settings()
        s2 = get_settings()

        assert s1 is s2

    def test_when_cache_clear_then_re_reads_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given cache cleared + env cambiado,
        When get_settings(),
        Then refleja el nuevo env.
        """
        monkeypatch.setenv('STAGE', 'dev')
        get_settings.cache_clear()
        s1 = get_settings()
        assert s1.stage == 'dev'

        monkeypatch.setenv('STAGE', 'prod')
        get_settings.cache_clear()
        s2 = get_settings()
        assert s2.stage == 'prod'
