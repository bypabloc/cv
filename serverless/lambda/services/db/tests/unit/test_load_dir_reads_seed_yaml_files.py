"""Helper seed_service._load_dir.

Given el directorio real seeds/data/experiences/,
When se invoca _load_dir('experiences'),
Then devuelve un (slug, data) por cada YAML, ordenado por filename, y el
slug se deriva del filename cuando el YAML no lo declara.
"""

import pytest

pytestmark = pytest.mark.unit


def test_load_dir_reads_seed_yaml_files() -> None:
    from services.seed_service import _load_dir

    # Act
    entries = _load_dir('experiences')

    # Assert
    slugs = [slug for slug, _data in entries]
    assert slugs == sorted(slugs)
    assert len(slugs) == 9
    assert 'destacame-architect' in slugs
    # Cada entry trae el dict del YAML con sus campos clave.
    by_slug = dict(entries)
    architect = by_slug['destacame-architect']
    assert architect['company'] == 'Destacame'
    assert architect['seniority'] == 'lead'


def test_load_dir_returns_empty_for_missing_directory() -> None:
    """Given un directorio de entidad inexistente,
    When se invoca _load_dir,
    Then devuelve una lista vacia (sin error).
    """
    from services.seed_service import _load_dir

    # Act
    entries = _load_dir('nonexistent_entity')

    # Assert
    assert entries == []
