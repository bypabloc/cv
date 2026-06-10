"""Helper seed_service._load_dir.

Given un directorio de snapshot con YAMLs de experiencias,
When se invoca _load_dir(data_dir, 'experiences'),
Then devuelve un (slug, data) por cada YAML, ordenado por filename, y el
slug se deriva del filename cuando el YAML no lo declara.
"""

import pytest

pytestmark = pytest.mark.unit


def test_load_dir_reads_seed_yaml_files(tmp_path) -> None:
    from services.seed_service import _load_dir

    # Arrange: 2 YAML, uno declara slug y el otro lo hereda del filename.
    folder = tmp_path / 'experiences'
    folder.mkdir()
    (folder / 'acme.yaml').write_text(
        'slug: acme\ncompany: Acme\nseniority: senior\n', encoding='utf-8'
    )
    (folder / 'beta.yaml').write_text(
        'company: Beta Corp\nseniority: lead\n', encoding='utf-8'
    )

    # Act
    entries = _load_dir(tmp_path, 'experiences')

    # Assert
    assert [slug for slug, _data in entries] == ['acme', 'beta']
    by_slug = dict(entries)
    assert by_slug['acme']['company'] == 'Acme'
    assert by_slug['beta']['seniority'] == 'lead'


def test_load_dir_returns_empty_for_missing_directory(tmp_path) -> None:
    """Given un directorio de entidad inexistente,
    When se invoca _load_dir,
    Then devuelve una lista vacia (sin error).
    """
    from services.seed_service import _load_dir

    # Act
    entries = _load_dir(tmp_path, 'nonexistent_entity')

    # Assert
    assert entries == []
