"""Modelos del ORM DynamoDB: uno por tabla del backend serverless.

Cada modelo es una subclase de `shared.dynamodb.base.BaseModel` con un
`Meta: TableMeta` que declara claves, TTL y GSIs.
"""

from shared.dynamodb.models.cache import CacheItem
from shared.dynamodb.models.contact import ContactItem
from shared.dynamodb.models.rate_limit_bucket import RateLimitBucketItem
from shared.dynamodb.models.rate_limit_rule import RateLimitRuleItem
from shared.dynamodb.models.tracking import TrackingEventItem

__all__ = [
    'CacheItem',
    'ContactItem',
    'RateLimitBucketItem',
    'RateLimitRuleItem',
    'TrackingEventItem',
]
