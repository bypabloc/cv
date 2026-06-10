"""shared.db.repositories.cv_write.link_niches.

Given una entidad con niches [generic, no-existe],
When se invoca link_niches,
Then borra la union previa y solo inserta la fila del niche conocido
(el slug desconocido se ignora sin fallar).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.models.cv.cv_entity import CertificateNiche
from shared.db.repositories.cv_write import link_niches

pytestmark = pytest.mark.unit


def test_cv_write_link_niches_rewrites_union_skipping_unknown() -> None:
    # Arrange
    session = MagicMock()
    niche_ids = {'generic': 'n-gen'}

    # Act
    link_niches(
        session,
        CertificateNiche,
        'certificate_id',
        'c-1',
        ['generic', 'no-existe'],
        niche_ids,
    )

    # Assert: 1 delete + 1 insert (el desconocido se salta)
    assert session.execute.call_count == 2
    insert_stmt = session.execute.call_args_list[1][0][0]
    params = insert_stmt.compile().params
    assert params['certificate_id'] == 'c-1'
    assert params['niche_id'] == 'n-gen'
