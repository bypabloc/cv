"""Helper seed_service._load_profile.

Given el archivo real seeds/data/profile.ts,
When se invoca _load_profile,
Then devuelve el dict del profile con stats, niches y URLs intactas
(las URLs con `//` no se truncan como comentario).
"""

import pytest

pytestmark = pytest.mark.unit


def test_load_profile_parses_stats_and_niches() -> None:
    from services.seed_service import _load_profile

    # Act
    profile = _load_profile()

    # Assert
    assert profile['stats'] == {
        'yearsExperience': 12,
        'companies': 8,
        'countries': 4,
        'certifications': 11,
    }
    assert profile['niches'] == [
        'fintech',
        'architect',
        'leader',
        'vibe',
        'generic',
    ]
    assert profile['avatarUrl'].startswith('https://')
    assert profile['contacts']['linkedin'].startswith('https://')
    assert profile['contacts']['github'].startswith('https://')
