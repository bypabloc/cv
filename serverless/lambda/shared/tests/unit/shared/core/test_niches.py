"""Unit tests para shared.core.niches.

Cubre AC-13 del plan sessions-normalize:
- ALL_NICHES exacto (6 niches incluye hub)
- CV_NICHES = ALL_NICHES - {hub} (5 niches)
- niche_from_origin valida + invalida + None
"""

from __future__ import annotations

import pytest

from shared.core.niches import ALL_NICHES, CV_NICHES, niche_from_origin

pytestmark = pytest.mark.unit


class TestNicheConstants:
    """ALL_NICHES y CV_NICHES — fuente unica de verdad."""

    def test_when_inspecting_all_niches_then_contains_6_subdomains(self) -> None:
        """
        Given el portfolio tiene 6 subdominios,
        When se inspecciona ALL_NICHES,
        Then es exactamente {hub, fintech, architect, leader, vibe, generic}.
        """
        assert ALL_NICHES == frozenset(
            {'hub', 'fintech', 'architect', 'leader', 'vibe', 'generic'},
        )

    def test_when_inspecting_cv_niches_then_excludes_hub(self) -> None:
        """
        Given hub es solo selector sin CV propio,
        When se inspecciona CV_NICHES,
        Then es ALL_NICHES sin hub (5 niches).
        """
        assert CV_NICHES == ALL_NICHES - {'hub'}
        assert 'hub' not in CV_NICHES
        assert len(CV_NICHES) == 5

    def test_when_inspecting_collections_then_frozensets(self) -> None:
        """
        Given ALL_NICHES y CV_NICHES son fuente unica,
        When se inspecciona el tipo,
        Then son frozenset (inmutables).
        """
        assert isinstance(ALL_NICHES, frozenset)
        assert isinstance(CV_NICHES, frozenset)


class TestNicheFromOrigin:
    """niche_from_origin(origin) — inferencia del header HTTP Origin."""

    @pytest.mark.parametrize(
        ('origin', 'expected'),
        [
            (
                'https://fintech.portfolio.dev.the-full-stack.com',
                'fintech',
            ),
            (
                'https://architect.portfolio.dev.the-full-stack.com',
                'architect',
            ),
            (
                'https://leader.portfolio.dev.the-full-stack.com',
                'leader',
            ),
            (
                'https://vibe.portfolio.dev.the-full-stack.com',
                'vibe',
            ),
            (
                'https://generic.portfolio.dev.the-full-stack.com',
                'generic',
            ),
            (
                'https://hub.portfolio.dev.the-full-stack.com',
                'hub',
            ),
            # Prod (sin .dev.)
            (
                'https://fintech.portfolio.the-full-stack.com',
                'fintech',
            ),
            (
                'https://hub.portfolio.the-full-stack.com',
                'hub',
            ),
        ],
    )
    def test_when_origin_is_valid_niche_then_returns_niche(
        self, origin: str, expected: str
    ) -> None:
        """
        Given un Origin con primer label = niche valido,
        When niche_from_origin lo recibe,
        Then retorna el niche.
        """
        assert niche_from_origin(origin) == expected

    def test_when_origin_is_apex_then_returns_none(self) -> None:
        """
        Given Origin del apex (the-full-stack.com sin subdominio niche),
        When niche_from_origin lo recibe,
        Then retorna None (no es un niche).
        """
        assert niche_from_origin('https://the-full-stack.com') is None

    def test_when_origin_is_www_then_returns_none(self) -> None:
        """
        Given Origin de www.the-full-stack.com,
        When niche_from_origin lo recibe,
        Then retorna None (www no esta en ALL_NICHES).
        """
        assert niche_from_origin('https://www.the-full-stack.com') is None

    def test_when_origin_is_localhost_then_returns_none(self) -> None:
        """
        Given Origin de localhost con puerto,
        When niche_from_origin lo recibe,
        Then retorna None.
        """
        assert niche_from_origin('https://localhost:9970') is None

    def test_when_origin_is_none_then_returns_none(self) -> None:
        """
        Given Origin None (header no presente),
        When niche_from_origin lo recibe,
        Then retorna None sin lanzar excepcion.
        """
        assert niche_from_origin(None) is None

    def test_when_origin_is_empty_string_then_returns_none(self) -> None:
        """
        Given Origin string vacio,
        When niche_from_origin lo recibe,
        Then retorna None.
        """
        assert niche_from_origin('') is None

    def test_when_origin_first_label_is_random_then_returns_none(self) -> None:
        """
        Given Origin con primer label que NO esta en ALL_NICHES,
        When niche_from_origin lo recibe,
        Then retorna None.
        """
        assert niche_from_origin('https://api.portfolio.the-full-stack.com') is None
        assert niche_from_origin('https://example.com') is None
