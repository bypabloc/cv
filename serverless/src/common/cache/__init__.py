"""
Cache module para Lambdas: DynamoDB TTL + SWR + lock distribuido.

Patron consolidado en `.claude/docs/dynamodb-cache/`. Reusable por todas
las Lambdas del backend.

Uso ergonomico (decorator):

    from common.cache import cached

    @cached(ttl=300, namespace='ssm', tags=['secrets'])
    def get_turnstile_secret() -> str:
        return ssm.get_parameter('/portfolio/turnstile-secret')['Value']

Uso bajo nivel (cliente directo):

    from common.cache import DynamoDBCache

    cache = DynamoDBCache(table_name='portfolio-cache-dev')
    cache.set('key', 'value', ttl=60)
    val = cache.get('key')
"""

from common.cache.client import DynamoDBCache
from common.cache.decorator import cached
from common.cache.types import CacheEntry, CacheStatus

__all__ = ['CacheEntry', 'CacheStatus', 'DynamoDBCache', 'cached']
