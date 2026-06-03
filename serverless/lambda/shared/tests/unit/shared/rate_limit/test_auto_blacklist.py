"""Tests para shared.rate_limit.auto_blacklist."""

from __future__ import annotations

import time

import boto3
import pytest
from shared.rate_limit.auto_blacklist import (
    AUTO_BLACKLIST_DURATION_SECONDS,
    AUTO_BLACKLIST_THRESHOLD,
    create_blacklist_rule,
    should_auto_blacklist,
)

pytestmark = pytest.mark.unit


class TestShouldAutoBlacklist:
    """should_auto_blacklist - decision boolean."""

    def test_when_below_threshold_then_false(self) -> None:
        """Given count=2 (< threshold), When check, Then False."""
        assert should_auto_blacklist(2) is False

    def test_when_at_threshold_then_true(self) -> None:
        """Given count == threshold, When check, Then True."""
        assert should_auto_blacklist(AUTO_BLACKLIST_THRESHOLD) is True

    def test_when_above_threshold_then_true(self) -> None:
        """Given count > threshold, When check, Then True."""
        assert should_auto_blacklist(AUTO_BLACKLIST_THRESHOLD + 1) is True

    def test_threshold_value_is_ten(self) -> None:
        """El threshold subio de 3 a 10: 3-9 CAPTCHAs NO blacklistean.

        Regresion del fix: un humano que reintenta un login (3-9 starts con
        CAPTCHA en 60s) ya NO se auto-blacklistea.
        """
        assert AUTO_BLACKLIST_THRESHOLD == 10
        assert should_auto_blacklist(3) is False
        assert should_auto_blacklist(9) is False
        assert should_auto_blacklist(10) is True

    def test_duration_is_one_hour(self) -> None:
        """La duracion del bloqueo bajo de 24h a 1h."""
        assert AUTO_BLACKLIST_DURATION_SECONDS == 3600


class TestCreateBlacklistRule:
    """create_blacklist_rule - persiste rule en DynamoDB."""

    def test_when_called_then_rule_persisted_with_default_ttl(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """
        Given IP,
        When create_blacklist_rule,
        Then rule en tabla con kind=ip_blacklist + expires_at ~ now + la
        duracion default (AUTO_BLACKLIST_DURATION_SECONDS = 1h).
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
