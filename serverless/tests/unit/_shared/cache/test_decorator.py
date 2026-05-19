"""Tests para _shared.cache.decorator (@cached)."""

from __future__ import annotations

import pytest

from _shared.cache.decorator import cached

pytestmark = pytest.mark.unit


class TestCachedDecorator:
    """@cached - memoizacion DynamoDB."""

    def test_when_called_twice_then_fn_invoked_once(
        self, cache_table: str
    ) -> None:
        """
        Given fn decorada con @cached,
        When llamada 2 veces seguidas con mismos args,
        Then fn solo se ejecuta 1 vez (segunda viene de cache).
        """
        call_count = [0]

        @cached(ttl=300, namespace='test')
        def compute(x: int) -> int:
            call_count[0] += 1
            return x * 2

        r1 = compute(5)
        r2 = compute(5)

        assert r1 == 10
        assert r2 == 10
        assert call_count[0] == 1  # solo 1 invocacion real

    def test_when_different_args_then_different_cache_keys(
        self, cache_table: str
    ) -> None:
        """
        Given fn decorada,
        When llamada con args diferentes,
        Then cada combinacion genera entry separado.
        """
        call_count = [0]

        @cached(ttl=300, namespace='test')
        def compute(x: int) -> int:
            call_count[0] += 1
            return x * 2

        compute(5)
        compute(10)
        compute(5)  # cache hit
        compute(10)  # cache hit

        assert call_count[0] == 2  # solo 2 invocaciones unicas

    def test_when_kwargs_change_then_different_cache_keys(
        self, cache_table: str
    ) -> None:
        """
        Given kwargs diferentes,
        When llamadas,
        Then se cachean por separado.
        """
        call_count = [0]

        @cached(ttl=300, namespace='test')
        def fetch(*, name: str) -> str:
            call_count[0] += 1
            return f'hello {name}'

        fetch(name='alice')
        fetch(name='bob')
        fetch(name='alice')  # hit

        assert call_count[0] == 2

    def test_when_fn_returns_complex_object_then_serialized_correctly(
        self, cache_table: str
    ) -> None:
        """
        Given fn que retorna dict/list,
        When @cached,
        Then roundtrip preserva la estructura.
        """
        @cached(ttl=300, namespace='test')
        def get_data() -> dict:
            return {'items': [1, 2, 3], 'meta': {'count': 3}}

        result = get_data()

        assert result == {'items': [1, 2, 3], 'meta': {'count': 3}}
        assert get_data() == result  # cache hit, mismo valor


class TestCachedWithTags:
    """@cached con tags + invalidate."""

    def test_when_cached_with_tags_then_invalidate_tag_clears_cache(
        self, cache_table: str
    ) -> None:
        """
        Given @cached(tags=['secrets']),
        When cache.invalidate(tag='secrets') + llamar fn,
        Then fn se vuelve a ejecutar (cache expired).
        """
        from _shared.cache.client import DynamoDBCache

        call_count = [0]

        @cached(ttl=300, namespace='ssm', tags=['secrets'])
        def get_secret() -> str:
            call_count[0] += 1
            return 'top-secret'

        get_secret()
        get_secret()  # hit
        assert call_count[0] == 1

        # Invalidar el tag
        cache = DynamoDBCache(table_name=cache_table)
        cache.invalidate(tag='secrets')

        get_secret()  # debe re-ejecutar
        assert call_count[0] == 2
