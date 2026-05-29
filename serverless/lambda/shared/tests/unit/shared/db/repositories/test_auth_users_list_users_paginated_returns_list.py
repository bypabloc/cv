"""
Given users en la tabla,
When se llama list_users_paginated,
Then retorna la lista de scalars del execute.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import list_users_paginated

pytestmark = pytest.mark.unit


def test_list_users_paginated_returns_scalars_list():
    # Arrange
    session = MagicMock()
    u1 = MagicMock()
    u2 = MagicMock()
    session.execute.return_value.scalars.return_value = [u1, u2]

    # Act
    result = list_users_paginated(session)

    # Assert
    assert result == [u1, u2]
