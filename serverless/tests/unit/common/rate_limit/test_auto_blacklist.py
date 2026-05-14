"""Tests para common.rate_limit.auto_blacklist."""

from __future__ import annotations

import time

import boto3
import pytest

from common.rate_limit.auto_blacklist import (
    AUTO_BLACKLIST_DURATION_SECONDS,
    AUTO_BLACKLIST_THRESHOLD,
    create_blacklist_rule,
    should_auto_blacklist,
)

pytestmark = pytest.mark.unit


class TestShouldAutoBlacklist:
    """should_auto_blacklist - decision boolean."""

    def test_when_below_threshold_then_false(self) -> None:
        """Given count=2, threshold=3, When check, Then False."""
        assert should_auto_blacklist(2) is False

    def test_when_at_threshold_then_true(self) -> None:
        """Given count=3, threshold=3, When check, Then True."""
        assert should_auto_blacklist(AUTO_BLACKLIST_THRESHOLD) is True

    def test_when_above_threshold_then_true(self) -> None:
        """Given count=5, threshold=3, When check, Then True."""
        assert should_auto_blacklist(5) is True


class TestCreateBlacklistRule:
    """create_blacklist_rule - persiste rule en DynamoDB."""

    def test_when_called_then_rule_persisted_with_24h_ttl(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """
        Given IP,
        When create_blacklist_rule,
        Then rule en tabla con kind=ip_blacklist + expires_at ~ now+86400.
        """
        before = int(time.time())
        create_blacklist_rule('1.2.3.4')

        table = boto3.resource('dynamodb', region_name='us-east-1').Table(
            'portfolio-rate-limit-rules-test'
        )
        result = table.get_item(
            Key={'rule_key': 'ip#1.2.3.4', 'kind': 'ip_blacklist'}
        )
        item = result.get('Item')
        assert item is not None
        assert item['action'] == 'block'
        assert int(item['expires_at']) - before >= AUTO_BLACKLIST_DURATION_SECONDS - 10
        assert int(item['expires_at']) - before <= AUTO_BLACKLIST_DURATION_SECONDS + 10

    def test_when_called_with_custom_duration_then_uses_it(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """Given duration=3600, When create, Then expires_at ~ now+3600."""
        before = int(time.time())
        create_blacklist_rule('1.2.3.5', duration_seconds=3600)

        table = boto3.resource('dynamodb', region_name='us-east-1').Table(
            'portfolio-rate-limit-rules-test'
        )
        result = table.get_item(
            Key={'rule_key': 'ip#1.2.3.5', 'kind': 'ip_blacklist'}
        )
        item = result.get('Item')
        assert item is not None
        assert int(item['expires_at']) - before >= 3590
        assert int(item['expires_at']) - before <= 3610
