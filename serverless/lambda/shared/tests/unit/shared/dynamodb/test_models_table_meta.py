"""
Given los 5 modelos del ORM,
When se inspecciona su TableMeta,
Then las claves/TTL/GSI coinciden con lo declarado en infra.yaml.

Un solo archivo por escenario: aqui el escenario es "el TableMeta de
cada modelo es correcto". Es la fuente de verdad que check_schema usa.
"""

from __future__ import annotations

from shared.dynamodb.models.cache import CacheItem
from shared.dynamodb.models.contact import ContactItem
from shared.dynamodb.models.rate_limit_bucket import RateLimitBucketItem
from shared.dynamodb.models.rate_limit_rule import RateLimitRuleItem
from shared.dynamodb.models.tracking import TrackingEventItem


def test_contact_item_meta() -> None:
    """ContactItem: PK simple `id`, sin SK, sin TTL, sin GSI."""
    meta = ContactItem.Meta
    assert meta.partition_key == 'id'
    assert meta.sort_key is None
    assert meta.ttl_attr is None
    assert meta.gsis == ()
    assert meta.table_default == 'portfolio-contacts-dev'


def test_tracking_event_item_meta() -> None:
    """TrackingEventItem: PK compuesta, TTL expires_at, 1 GSI."""
    meta = TrackingEventItem.Meta
    assert meta.partition_key == 'session_id'
    assert meta.sort_key == 'page_id'
    assert meta.ttl_attr == 'expires_at'
    assert len(meta.gsis) == 1
    gsi = meta.gsis[0]
    assert gsi.name == 'niche-created_at-index'
    assert gsi.partition_key == 'niche'
    assert gsi.sort_key == 'created_at'


def test_cache_item_meta() -> None:
    """CacheItem: PK simple `cache_key`, TTL expires_at."""
    meta = CacheItem.Meta
    assert meta.partition_key == 'cache_key'
    assert meta.sort_key is None
    assert meta.ttl_attr == 'expires_at'
    assert meta.gsis == ()


def test_rate_limit_bucket_item_meta() -> None:
    """RateLimitBucketItem: PK simple `bucket_key`, TTL expires_at."""
    meta = RateLimitBucketItem.Meta
    assert meta.partition_key == 'bucket_key'
    assert meta.sort_key is None
    assert meta.ttl_attr == 'expires_at'


def test_rate_limit_rule_item_meta() -> None:
    """RateLimitRuleItem: PK compuesta rule_key + kind, TTL expires_at."""
    meta = RateLimitRuleItem.Meta
    assert meta.partition_key == 'rule_key'
    assert meta.sort_key == 'kind'
    assert meta.ttl_attr == 'expires_at'


def test_key_attributes_includes_gsi_keys() -> None:
    """key_attributes() incluye las keys de la tabla y del GSI."""
    attrs = TrackingEventItem.Meta.key_attributes()
    assert attrs == {'session_id', 'page_id', 'niche', 'created_at'}
