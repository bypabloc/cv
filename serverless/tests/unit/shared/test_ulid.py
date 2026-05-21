"""Unit tests para shared.ulid (UUIDv7 generator)."""

from __future__ import annotations

import time

import pytest

from shared.ulid import new_uuidv7

pytestmark = pytest.mark.unit


class TestNewUUIDv7:
    """new_uuidv7 - UUIDv7 sortable por timestamp."""

    def test_when_called_then_returns_36_char_uuid_with_dashes(self) -> None:
        """
        Given runtime normal,
        When new_uuidv7() es invocado,
        Then retorna string 36 chars con 4 dashes en posiciones canonicas.
        """
        uid = new_uuidv7()

        assert len(uid) == 36
        assert uid[8] == '-'
        assert uid[13] == '-'
        assert uid[18] == '-'
        assert uid[23] == '-'

    def test_when_called_then_version_byte_is_7(self) -> None:
        """
        Given UUIDv7 RFC 9562,
        When new_uuidv7() es invocado,
        Then el primer char del 3er grupo es '7' (version marker).
        """
        uid = new_uuidv7()

        # Position 14 (0-indexed) en string formato: xxxxxxxx-xxxx-Vxxx-...
        assert uid[14] == '7'

    def test_when_called_then_variant_bits_are_10(self) -> None:
        """
        Given UUIDv7 RFC 4122 variant,
        When new_uuidv7() es invocado,
        Then primer char del 4to grupo es 8/9/a/b (variant 10xx).
        """
        uid = new_uuidv7()

        # Position 19 en string formato: ...-xxxx-Vxxx-... debe ser 8|9|a|b
        assert uid[19] in '89ab'

    def test_when_called_1000_times_then_all_unique(self) -> None:
        """
        Given runtime normal,
        When new_uuidv7() es invocado 1000 veces,
        Then los 1000 UUIDs son unicos.
        """
        uids = [new_uuidv7() for _ in range(1000)]

        assert len(set(uids)) == 1000

    def test_when_called_sequentially_then_lexicographic_order_matches_time(
        self,
    ) -> None:
        """
        Given 2 UUIDs generados con delta de 10ms,
        When se comparan como strings,
        Then el segundo es mayor que el primero (sortable property).
        """
        first = new_uuidv7()
        time.sleep(0.01)  # 10ms
        second = new_uuidv7()

        assert second > first
