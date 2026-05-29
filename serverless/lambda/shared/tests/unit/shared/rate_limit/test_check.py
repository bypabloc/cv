"""Tests para shared.rate_limit.check (API publica check_or_raise)."""

from __future__ import annotations

import time

import boto3
import pytest
from shared.cache.client import DynamoDBCache
from shared.rate_limit.check import check_or_raise
from shared.rate_limit.exceptions import (
    CountryBlockedError,
    IPBlacklistedError,
    RateLimitExceededError,
)

pytestmark = pytest.mark.unit


def _add_endpoint_rule(
    *, endpoint: str, limit: int, window_seconds: int, action: str = 'throttle'
) -> None:
    """Helper para crear rule endpoint en la tabla test."""
    table = boto3.resource('dynamodb', region_name='us-east-1').Table(
        'portfolio-rate-limit-rules-test'
    )
    table.put_item(
        Item={
            'rule_key': f'endpoint#{endpoint}',
            'kind': 'endpoint',
            'limit': limit,
            'window_seconds': window_seconds,
            'action': action,
        },
    )
    # Invalidar cache de rules para que pick-up el cambio
    DynamoDBCache(table_name='portfolio-cache-test').invalidate(tag='rate-limit-rules')


def _add_ip_rule(*, ip: str, kind: str, reason: str = '') -> None:
    """Helper para crear rule IP whitelist/blacklist."""
    table = boto3.resource('dynamodb', region_name='us-east-1').Table(
        'portfolio-rate-limit-rules-test'
    )
    table.put_item(
        Item={
            'rule_key': f'ip#{ip}',
            'kind': kind,
            'action': 'block' if kind == 'ip_blacklist' else 'allow',
            'reason': reason or kind,
        },
    )
    DynamoDBCache(table_name='portfolio-cache-test').invalidate(tag='rate-limit-rules')


def _add_country_rule(*, country: str, action: str = 'block') -> None:
    table = boto3.resource('dynamodb', region_name='us-east-1').Table(
        'portfolio-rate-limit-rules-test'
    )
    table.put_item(
        Item={
            'rule_key': f'country#{country}',
            'kind': 'country',
            'action': action,
            'reason': f'{country} {action}',
        },
    )
    DynamoDBCache(table_name='portfolio-cache-test').invalidate(tag='rate-limit-rules')


class TestRateLimit:
    """check_or_raise - rate limit basico."""

    def test_when_under_limit_then_allowed(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """Given limit=3, first 3 calls, When check, Then allowed."""
        _add_endpoint_rule(endpoint='/contact', limit=3, window_seconds=60)
        now = int(time.time())

        for _ in range(3):
            decision = check_or_raise(
                ip='1.2.3.4', endpoint='/contact', now=now,
            )
            assert decision['allowed'] is True

    def test_when_over_limit_then_raises(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """Given limit=3 + 3 calls done, When 4th call, Then RateLimitExceededError."""
        _add_endpoint_rule(endpoint='/contact', limit=3, window_seconds=60)
        now = int(time.time())

        for _ in range(3):
            check_or_raise(ip='1.2.3.4', endpoint='/contact', now=now)

        with pytest.raises(RateLimitExceededError) as exc_info:
            check_or_raise(ip='1.2.3.4', endpoint='/contact', now=now)

        assert exc_info.value.code == 'RATE_LIMIT_EXCEEDED'
        assert exc_info.value.retry_after_seconds > 0


class TestIPWhitelist:
    """check_or_raise - IP whitelist skip."""

    def test_when_ip_whitelisted_then_allowed_regardless_of_count(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """
        Given IP en whitelist + limit=1 (estricto),
        When 100 calls,
        Then todas allowed.
        """
        _add_endpoint_rule(endpoint='/contact', limit=1, window_seconds=60)
        _add_ip_rule(ip='1.2.3.4', kind='ip_whitelist')
        now = int(time.time())

        for _ in range(100):
            decision = check_or_raise(
                ip='1.2.3.4', endpoint='/contact', now=now,
            )
            assert decision['allowed'] is True
            assert decision['reason'] == 'ip_whitelist'


class TestIPBlacklist:
    """check_or_raise - IP blacklist."""

    def test_when_ip_blacklisted_then_raises_immediately(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """
        Given IP en blacklist,
        When check,
        Then IPBlacklistedError sin tocar bucket.
        """
        _add_ip_rule(ip='1.2.3.4', kind='ip_blacklist', reason='manual ban')

        with pytest.raises(IPBlacklistedError) as exc_info:
            check_or_raise(ip='1.2.3.4', endpoint='/contact', now=int(time.time()))

        assert exc_info.value.code == 'IP_BLACKLISTED'


class TestCountryBlock:
    """check_or_raise - country block."""

    def test_when_country_blocked_then_raises(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """Given country=CN action=block, When check, Then CountryBlockedError."""
        _add_country_rule(country='CN', action='block')

        with pytest.raises(CountryBlockedError) as exc_info:
            check_or_raise(
                ip='1.2.3.4',
                endpoint='/contact',
                country='CN',
                now=int(time.time()),
            )

        assert exc_info.value.code == 'COUNTRY_BLOCKED'

    def test_when_country_throttle_action_then_does_not_block(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """
        Given country rule action != block,
        When check,
        Then no levanta (sigue al endpoint rule).
        """
        _add_country_rule(country='CN', action='throttle')

        # Sin endpoint rule, deberia continuar y allowed
        decision = check_or_raise(
            ip='1.2.3.4',
            endpoint='/contact',
            country='CN',
            now=int(time.time()),
        )

        assert decision['allowed'] is True


class TestAutoBlacklist:
    """Auto-blacklist por 3+ turnstile tokens en 60s."""

    def test_when_3_turnstile_tokens_then_blacklist_rule_created(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """
        Given limit alto + turnstile_validated=True en 3 calls,
        When 3 calls,
        Then se crea ip_blacklist rule.
        """
        _add_endpoint_rule(endpoint='/contact', limit=100, window_seconds=60)
        now = int(time.time())

        for _ in range(3):
            check_or_raise(
                ip='2.3.4.5',
                endpoint='/contact',
                turnstile_validated=True,
                now=now,
            )

        # Verificar que la rule ip_blacklist se creo
        table = boto3.resource('dynamodb', region_name='us-east-1').Table(
            'portfolio-rate-limit-rules-test'
        )
        result = table.get_item(
            Key={'rule_key': 'ip#2.3.4.5', 'kind': 'ip_blacklist'}
        )
        item = result.get('Item')
        assert item is not None
        assert item.get('action') == 'block'
