"""Unit tests para shared.aws.ssm.get_parameter_by_name (catalog-aware).

Variante de get_secret_by_name para parametros String planos (sin KMS):
la clave PUBLICA del bypass de Turnstile es publica, no requiere decrypt.
"""

from __future__ import annotations

import pytest
from moto import mock_aws
from shared.aws.ssm import clear_cache, get_parameter_by_name

pytestmark = pytest.mark.unit


class TestCloudMode:
    """Cuando SSM_<UPPER>_PATH esta seteado, lee de SSM con get_parameter."""

    @mock_aws
    def test_when_ssm_path_env_set_reads_string_param(self, monkeypatch):
        import boto3

        ssm = boto3.client('ssm', region_name='us-east-1')
        ssm.put_parameter(
            Name='/portfolio/dev/turnstile-bypass-public-key',
            Value='pub-key-b64-value',
            Type='String',
        )
        monkeypatch.setenv(
            'SSM_TURNSTILE_BYPASS_PUBLIC_KEY_PATH',
            '/portfolio/dev/turnstile-bypass-public-key',
        )
        clear_cache()

        result = get_parameter_by_name('turnstile-bypass-public-key')

        assert result == 'pub-key-b64-value'


class TestLocalMode:
    """Cuando SSM_<UPPER>_PATH NO esta, lee del env local."""

    def test_with_explicit_local_env_param(self, monkeypatch):
        monkeypatch.delenv(
            'SSM_TURNSTILE_BYPASS_PUBLIC_KEY_PATH', raising=False
        )
        monkeypatch.setenv('TURNSTILE_BYPASS_PUBLIC_KEY', 'local-pub-key')

        result = get_parameter_by_name(
            'turnstile-bypass-public-key',
            local_env='TURNSTILE_BYPASS_PUBLIC_KEY',
        )

        assert result == 'local-pub-key'


class TestErrors:
    """Sin ninguna env var seteada: error claro listando candidatos."""

    def test_when_no_env_vars_raises(self, monkeypatch):
        monkeypatch.delenv(
            'SSM_TURNSTILE_BYPASS_PUBLIC_KEY_PATH', raising=False
        )
        monkeypatch.delenv('TURNSTILE_BYPASS_PUBLIC_KEY', raising=False)

        with pytest.raises(RuntimeError, match='No se puede resolver'):
            get_parameter_by_name(
                'turnstile-bypass-public-key',
                local_env='TURNSTILE_BYPASS_PUBLIC_KEY',
            )

    def test_error_message_lists_candidates(self, monkeypatch):
        monkeypatch.delenv(
            'SSM_TURNSTILE_BYPASS_PUBLIC_KEY_PATH', raising=False
        )
        monkeypatch.delenv('TURNSTILE_BYPASS_PUBLIC_KEY', raising=False)

        with pytest.raises(RuntimeError) as exc_info:
            get_parameter_by_name(
                'turnstile-bypass-public-key',
                local_env='TURNSTILE_BYPASS_PUBLIC_KEY',
            )

        msg = str(exc_info.value)
        assert 'SSM_TURNSTILE_BYPASS_PUBLIC_KEY_PATH' in msg
        assert 'TURNSTILE_BYPASS_PUBLIC_KEY' in msg
