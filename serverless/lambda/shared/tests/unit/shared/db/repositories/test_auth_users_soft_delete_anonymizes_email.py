"""
Given un user existente con una sesion (family fam1),
When se llama soft_delete_user con un anonymized_email,
Then setea deleted_at, anonimiza el email, status=DELETED y retorna
los family_id borrados.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models.auth.enums import AuthUserStatus
from shared.db.repositories.auth_users import soft_delete_user

pytestmark = pytest.mark.unit


def test_soft_delete_user_anonymizes_and_returns_families():
    # Arrange
    session = MagicMock()
    user = MagicMock()
    session.execute.return_value.scalars.return_value = ['fam1']
    session.get.return_value = user

    # Act
    families = soft_delete_user(
        session,
        user_id='u1',
        anonymized_email='deleted-u@invalid.local',
    )

    # Assert
    assert families == ['fam1']
    assert user.deleted_at is not None
    assert user.email == 'deleted-u@invalid.local'
    assert user.status == AuthUserStatus.DELETED
    session.flush.assert_called_once()
