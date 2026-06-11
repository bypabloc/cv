"""Service cv_service — cache HIT no toca el repository (ni Neon).

Given una entrada FRESH en el cache de DynamoDB para get_full_cv,
When se invoca cv_service.get_full_cv,
Then devuelve el valor cacheado y NO llama a la query de Neon.
"""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


def test_cv_service_returns_cached_value_without_touching_repository(
    monkeypatch,
):
    from services import cv_service

    # Arrange: una entrada FRESH en el cache (expira lejos en el futuro).
    fake_cache = MagicMock()
    fake_cache.table = 'cv-cache-test'
    fake_cache.get_entry.return_value = {
        'value': '{"profile": {"cached": true}}',
        'encoding': 'json',
        'expires_at': 9_999_999_999,
        'stale_until': 9_999_999_999,
    }
    monkeypatch.setattr(
        'shared.cache.decorator.DynamoDBCache', lambda: fake_cache
    )

    # Act + Assert: el repository NO se invoca (cache HIT).
    with patch('services.cv_service._get_full_cv') as mock_repo:
        result = cv_service.get_full_cv(niche='fintech', locale='es')

    assert result == {'profile': {'cached': True}}
    mock_repo.assert_not_called()
