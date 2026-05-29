"""Unit tests para shared.aws.ssm (Powertools parameters + cache)."""

from __future__ import annotations

import pytest
from moto import mock_aws
from shared.aws.ssm import clear_cache, get_parameter, get_secret

pytestmark = pytest.mark.unit


@mock_aws
class TestGetSecret:
    """get_secret - SSM SecureString con KMS decrypt + cache."""

    def test_when_secret_exists_then_returns_decrypted_value(self) -> None:
        """
        Given SSM SecureString creado,
        When get_secret(path),
        Then retorna valor decrypted.
        """
        import boto3

        ssm = boto3.client('ssm', region_name='us-east-1')
        ssm.put_parameter(
            Name='/test/secret',
            Value='supersecret',
            Type='SecureString',
        )

        clear_cache()
        result = get_secret('/test/secret')

        assert result == 'supersecret'

    def test_when_called_twice_then_second_call_uses_cache(self) -> None:
        """
        Given get_secret llamado 2 veces consecutivas,
        When,
        Then segunda llamada lee de cache Powertools (no llama SSM API).

        Verificacion: cambiar el valor en SSM directamente; si cache
        funciona, la segunda llamada retorna el valor original.
        """
        import boto3

        ssm = boto3.client('ssm', region_name='us-east-1')
        ssm.put_parameter(
            Name='/test/cached',
            Value='original',
            Type='SecureString',
        )

        clear_cache()
        first = get_secret('/test/cached', max_age=300)

        # Cambiar SSM directamente sin invalidar el cache local
        ssm.put_parameter(
            Name='/test/cached',
            Value='changed',
            Type='SecureString',
            Overwrite=True,
        )

        second = get_secret('/test/cached', max_age=300)

        assert first == 'original'
        assert second == 'original'  # cache hit, no refleja el cambio

    def test_when_path_missing_then_raises(self) -> None:
        """
        Given path SSM no existente,
        When get_secret,
        Then raises (Powertools GetParameterError).
        """
        clear_cache()

        with pytest.raises(Exception):  # noqa: B017
            get_secret('/missing/path')


@mock_aws
class TestGetParameter:
    """get_parameter - SSM String simple sin decrypt."""

    def test_when_string_param_exists_then_returns_value(self) -> None:
        """
        Given SSM String,
        When get_parameter(path),
        Then retorna valor plain.
        """
        import boto3

        ssm = boto3.client('ssm', region_name='us-east-1')
        ssm.put_parameter(
            Name='/test/email',
            Value='owner@example.com',
            Type='String',
        )

        clear_cache()
        result = get_parameter('/test/email')

        assert result == 'owner@example.com'
