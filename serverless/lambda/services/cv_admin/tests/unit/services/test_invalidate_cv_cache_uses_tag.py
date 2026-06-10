"""invalidate_cv_cache invalida por tag 'cv' (el de @cached del Lambda cv).

Given el cliente de cache mockeado,
When se invoca content_service.invalidate_cv_cache,
Then llama DynamoDBCache().invalidate(tag='cv') y devuelve el conteo.
"""

from unittest.mock import MagicMock


def test_invalidate_cv_cache_uses_tag(monkeypatch):
    from services import content_service

    cache = MagicMock()
    cache.invalidate.return_value = 7
    monkeypatch.setattr(content_service, 'DynamoDBCache', lambda: cache)

    result = content_service.invalidate_cv_cache()

    assert result == 7
    cache.invalidate.assert_called_once_with(tag='cv')
