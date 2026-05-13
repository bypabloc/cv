"""Unit tests para devtools/verify/flags.py."""

from __future__ import annotations

import pytest

from verify.flags import flag


pytestmark = pytest.mark.unit


class TestFlagDefaults:
    """Defaults aplicados cuando no se pasan flags."""

    def test_no_source_defaults_to_all_changed(self) -> None:
        """Si no se especifica source, default es all_changed=True."""
        result = flag({})
        assert result['all_changed'] is True
        assert result['staged'] is False
        assert result['modified'] is False

    def test_execute_defaults_false(self) -> None:
        result = flag({})
        assert result['execute'] is False

    def test_json_defaults_false(self) -> None:
        result = flag({})
        assert result['json'] is False


class TestFlagValidation:
    """Validación de combinaciones de flags."""

    def test_staged_only(self) -> None:
        result = flag({'staged': True})
        assert result['staged'] is True
        assert result['all_changed'] is False

    def test_modified_only(self) -> None:
        result = flag({'modified': True})
        assert result['modified'] is True
        assert result['all_changed'] is False

    def test_all_changed_explicit(self) -> None:
        result = flag({'all_changed': True})
        assert result['all_changed'] is True

    def test_two_sources_raises(self) -> None:
        """Combinar dos fuentes es inválido."""
        with pytest.raises(ValueError, match='Solo se permite UNA fuente'):
            flag({'staged': True, 'modified': True})

    def test_three_sources_raises(self) -> None:
        with pytest.raises(ValueError, match='Solo se permite UNA fuente'):
            flag(
                {
                    'staged': True,
                    'modified': True,
                    'all_changed': True,
                },
            )

    def test_invalid_flag_raises(self) -> None:
        with pytest.raises(ValueError, match='invalid_flag'):
            flag({'invalid_flag': True})

    def test_execute_and_json_combinable(self) -> None:
        """--execute y --json se combinan sin problema."""
        result = flag({'staged': True, 'execute': True, 'json': True})
        assert result['execute'] is True
        assert result['json'] is True
