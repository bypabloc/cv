"""
Given sin DATABASE_URL pero con SSM_NEON_URL_PATH apuntando a un SecureString,
When resolve_database_url corre,
Then lee el secreto de SSM (moto) y lo normaliza al driver psycopg v3.
"""

from __future__ import annotations

import pytest
from moto import mock_aws
from shared.aws.ssm import clear_cache
from shared.db.url import resolve_database_url

pytestmark = pytest.mark.integration


@mock_aws
def test_resolve_url_from_ssm_e2e(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sin DATABASE_URL, resolve_database_url lee la URL de SSM."""
    # Arrange
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.setenv('SSM_NEON_URL_PATH', '/portfolio/dev/neon-url')
    import boto3

    boto3.client('ssm', region_name='us-east-1').put_parameter(
        Name='/portfolio/dev/neon-url',
        Value='postgresql://neon:pw@ep-pooler.neon.tech/portfolio',
        Type='SecureString',
    )
    clear_cache()

    # Act
    url = resolve_database_url()

    # Assert
    assert url == ('postgresql+psycopg://neon:pw@ep-pooler.neon.tech/portfolio')
