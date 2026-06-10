"""shared.aws.s3.list_keys.

Given un bucket cuyo list_objects_v2 pagina en 2 paginas (una de ellas
sin Contents),
When se invoca list_keys,
Then concatena las keys de todas las paginas en orden y tolera paginas
vacias.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from shared.aws.s3 import list_keys

pytestmark = pytest.mark.unit


def test_s3_list_keys_paginates() -> None:
    # Arrange
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {'Contents': [{'Key': 'latest/profile.yaml'}]},
        {},
        {'Contents': [{'Key': 'latest/experiences/acme.yaml'}]},
    ]
    client = MagicMock()
    client.get_paginator.return_value = paginator

    # Act
    with patch('shared.aws.s3.get_client', return_value=client):
        keys = list_keys('portfolio-db-backups-dev', 'latest/')

    # Assert
    assert keys == [
        'latest/profile.yaml',
        'latest/experiences/acme.yaml',
    ]
    assert paginator.paginate.call_args.kwargs == {
        'Bucket': 'portfolio-db-backups-dev',
        'Prefix': 'latest/',
    }
