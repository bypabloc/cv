"""Descarga del snapshot S3 (seed_service._download_snapshot).

Given un prefijo S3 con keys YAML (y una key no-YAML que se ignora),
When se descarga el snapshot,
Then reconstruye el layout relativo bajo un tempdir local; y un prefijo
sin YAML alguno falla con un error explicito.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_seed_download_snapshot_writes_layout():
    from services.seed_service import _download_snapshot

    # Arrange
    keys = [
        'latest/profile.yaml',
        'latest/experiences/acme.yaml',
        'latest/manifest.json',
    ]
    contents = {
        'latest/profile.yaml': 'handle: bypabloc\n',
        'latest/experiences/acme.yaml': 'slug: acme\n',
    }

    with (
        patch(
            'shared.aws.s3.list_keys', return_value=keys
        ) as list_mock,
        patch(
            'shared.aws.s3.get_object_text',
            side_effect=lambda bucket, key: contents[key],
        ),
    ):
        # Act
        target = _download_snapshot('s3://portfolio-db-backups-dev/latest')

    # Assert
    assert list_mock.call_args[0] == ('portfolio-db-backups-dev', 'latest/')
    assert (target / 'profile.yaml').read_text() == 'handle: bypabloc\n'
    assert (
        target / 'experiences' / 'acme.yaml'
    ).read_text() == 'slug: acme\n'
    assert not (target / 'manifest.json').exists()


def test_seed_download_snapshot_fails_on_empty_prefix():
    """Given un prefijo sin keys YAML,
    When se descarga el snapshot,
    Then falla con ValueError explicito (no hay nada que restaurar).
    """
    from services.seed_service import _download_snapshot

    with (
        patch('shared.aws.s3.list_keys', return_value=[]),
        pytest.raises(ValueError, match='no contiene YAML'),
    ):
        _download_snapshot('s3://portfolio-db-backups-dev/latest/')
