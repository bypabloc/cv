"""Unit tests para shared.aws.ssm.get_secret_by_name (catalog-aware)."""

from __future__ import annotations

import pytest
from moto import mock_aws
from shared.aws.ssm import clear_cache, get_secret_by_name

pytestmark = pytest.mark.unit


class TestCloudMode:
    """Cuando SSM_<UPPER>_PATH esta seteado, lee de SSM."""

    @mock_aws
    def test_when_ssm_path_env_set_reads_from_ssm(self, monkeypatch):
        import boto3

        ssm = boto3.client('ssm', region_name='us-east-1')
        ssm.put_parameter(
            Name='/portfolio/dev/turnstile-secret',
            Value='cloud-secret-value',
            Type='SecureString',
        )

        monkeypatch.setenv(
            'SSM_TURNSTILE_SECRET_PATH',
            '/portfolio/dev/turnstile-secret',
        )
        clear_cache()
        result = get_secret_by_name('turnstile-secret')

        assert result == 'cloud-secret-value'

    @mock_aws
    def test_when_ssm_path_set_for_neon_url(self, monkeypatch):
        import boto3

        ssm = boto3.client('ssm', region_name='us-east-1')
        ssm.put_parameter(
            Name='/portfolio/dev/neon-url',
            Value='postgresql://user:pwd@host/db',
            Type='SecureString',
        )
        monkeypatch.setenv(
            'SSM_NEON_URL_PATH',
            '/portfolio/dev/neon-url',
        )
        clear_cache()

        result = get_secret_by_name('neon-url')

        assert result == 'postgresql://user:pwd@host/db'


class TestLocalMode:
    """Cuando SSM_<UPPER>_PATH NO esta, lee del env local."""

    def test_with_explicit_local_env_param(self, monkeypatch):
        monkeypatch.delenv('SSM_TURNSTILE_SECRET_PATH', raising=False)
        monkeypatch.setenv('TURNSTILE_SECRET_KEY', 'local-from-dotenv')

        result = get_secret_by_name(
            'turnstile-secret',
            local_env='TURNSTILE_SECRET_KEY',
        )

        assert result == 'local-from-dotenv'

    def test_falls_back_to_secret_upper_convention(self, monkeypatch):
        monkeypatch.delenv('SSM_TURNSTILE_SECRET_PATH', raising=False)
        monkeypatch.delenv('TURNSTILE_SECRET_KEY', raising=False)
        monkeypatch.setenv('SECRET_TURNSTILE_SECRET', 'from-convention')

        result = get_secret_by_name('turnstile-secret')

        assert result == 'from-convention'

    def test_prefers_local_env_over_secret_convention(self, monkeypatch):
        monkeypatch.delenv('SSM_TURNSTILE_SECRET_PATH', raising=False)
        monkeypatch.setenv('TURNSTILE_SECRET_KEY', 'primary')
        monkeypatch.setenv('SECRET_TURNSTILE_SECRET', 'fallback')

        result = get_secret_by_name(
            'turnstile-secret',
            local_env='TURNSTILE_SECRET_KEY',
        )

        assert result == 'primary'


class TestErrors:
    """Sin ninguna env var setteada: error claro."""

    def test_when_no_env_vars_raises(self, monkeypatch):
        monkeypatch.delenv('SSM_TURNSTILE_SECRET_PATH', raising=False)
        monkeypatch.delenv('TURNSTILE_SECRET_KEY', raising=False)
        monkeypatch.delenv('SECRET_TURNSTILE_SECRET', raising=False)

        with pytest.raises(RuntimeError, match='No se puede resolver'):
            get_secret_by_name(
                'turnstile-secret',
                local_env='TURNSTILE_SECRET_KEY',
            )

    def test_error_message_lists_candidates(self, monkeypatch):
        monkeypatch.delenv('SSM_NEON_URL_PATH', raising=False)
        monkeypatch.delenv('DB_URL', raising=False)
        monkeypatch.delenv('SECRET_NEON_URL', raising=False)

        with pytest.raises(RuntimeError) as exc_info:
            get_secret_by_name('neon-url', local_env='DB_URL')

        msg = str(exc_info.value)
        assert 'SSM_NEON_URL_PATH' in msg
        assert 'DB_URL' in msg
        assert 'SECRET_NEON_URL' in msg
