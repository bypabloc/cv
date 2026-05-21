"""Tests para shared.rate_limit.buckets (sliding window weighted)."""

from __future__ import annotations

import pytest

from shared.rate_limit.buckets import (
    _window_start,
    get_effective_count,
    increment_bucket,
)

pytestmark = pytest.mark.unit


class TestWindowStart:
    """_window_start - round down a multiplo de N."""

    def test_when_now_in_middle_then_returns_floor(self) -> None:
        """Given now=1500, window=60, When _window_start, Then 1500//60*60 = 1500."""
        assert _window_start(1500, 60) == 1500

    def test_when_now_offset_then_floors(self) -> None:
        """Given now=1530, window=60, When _window_start, Then 1500."""
        assert _window_start(1530, 60) == 1500


class TestIncrementBucket:
    """increment_bucket - atomic ADD."""

    def test_when_first_increment_then_count_is_1(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """Given bucket vacio, When increment, Then count=1."""
        result = increment_bucket(
            ip='1.2.3.4',
            endpoint='/contact',
            window_seconds=60,
            now=1500,
        )

        assert result['count'] == 1
        assert result['turnstile_tokens'] == 0

    def test_when_multiple_increments_then_count_accumulates(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """Given 3 increments same bucket, When done, Then count=3."""
        for _ in range(3):
            increment_bucket(
                ip='1.2.3.4',
                endpoint='/contact',
                window_seconds=60,
                now=1500,
            )

        # Despues de 3 increments, leer el effective count del bucket actual
        effective = get_effective_count(
            ip='1.2.3.4',
            endpoint='/contact',
            window_seconds=60,
            now=1500,
        )
        # Bucket previous esta vacio, current=3, elapsed=0 -> effective=3
        assert effective == 3.0

    def test_when_turnstile_validated_then_turnstile_tokens_incremented(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """
        Given turnstile_validated=True,
        When increment,
        Then turnstile_tokens incrementado.
        """
        result = increment_bucket(
            ip='1.2.3.4',
            endpoint='/contact',
            window_seconds=60,
            turnstile_validated=True,
            now=1500,
        )

        assert result['count'] == 1
        assert result['turnstile_tokens'] == 1


class TestGetEffectiveCount:
    """get_effective_count - sliding window weighted."""

    def test_when_no_buckets_then_zero(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """Given no buckets, When get_effective_count, Then 0."""
        result = get_effective_count(
            ip='1.2.3.4',
            endpoint='/contact',
            window_seconds=60,
            now=1500,
        )

        assert result == 0.0

    def test_when_only_current_bucket_then_returns_count(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """Given solo current bucket con count=5, When effective, Then 5."""
        # Simulate 5 requests at start of window
        for _ in range(5):
            increment_bucket(
                ip='1.2.3.4',
                endpoint='/contact',
                window_seconds=60,
                now=1500,
            )

        # Read at start of window (elapsed=0, previous_weight=1.0 pero previous=0)
        effective = get_effective_count(
            ip='1.2.3.4',
            endpoint='/contact',
            window_seconds=60,
            now=1500,
        )

        assert effective == 5.0

    def test_when_previous_bucket_present_then_weighted_sum(
        self, rate_limit_tables: dict[str, str]
    ) -> None:
        """
        Given previous bucket count=10 + current bucket count=4 + elapsed=30s,
        When effective,
        Then 4 + 10*(1 - 30/60) = 4 + 5 = 9.0.
        """
        # Previous bucket: window 1440-1500, count=10
        for _ in range(10):
            increment_bucket(
                ip='1.2.3.4', endpoint='/contact', window_seconds=60, now=1440,
            )
        # Current bucket: window 1500-1560, count=4
        for _ in range(4):
            increment_bucket(
                ip='1.2.3.4', endpoint='/contact', window_seconds=60, now=1500,
            )

        # Leer 30s elapsed en el bucket actual (1530)
        effective = get_effective_count(
            ip='1.2.3.4',
            endpoint='/contact',
            window_seconds=60,
            now=1530,
        )

        assert effective == 9.0
