"""Helper seed_service._load_profile.

Given un snapshot con profile.yaml (el formato que escribe db_export),
When se invoca _load_profile(data_dir),
Then devuelve el dict del profile con stats, niches y contacts intactos.
"""

import pytest

pytestmark = pytest.mark.unit

_PROFILE_YAML = """\
name: Pablo Contreras
handle: bypabloc
location: Santiago, Chile
avatarUrl: https://example.com/avatar.avif
contacts:
  email: user@example.com
  linkedin: https://linkedin.com/in/bypabloc
  github: https://github.com/bypabloc
headline:
  es: Senior Full Stack
  en: Senior Full Stack
summary:
  es: Resumen
  en: Summary
stats:
  yearsExperience: 12
  companies: 8
  countries: 4
  certifications: 11
niches:
  - fintech
  - architect
  - leader
  - vibe
  - generic
"""


def test_load_profile_parses_stats_and_niches(tmp_path) -> None:
    from services.seed_service import _load_profile

    # Arrange
    (tmp_path / 'profile.yaml').write_text(_PROFILE_YAML, encoding='utf-8')

    # Act
    profile = _load_profile(tmp_path)

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
    assert profile['avatarUrl'] == 'https://example.com/avatar.avif'
    assert profile['contacts']['github'] == 'https://github.com/bypabloc'
