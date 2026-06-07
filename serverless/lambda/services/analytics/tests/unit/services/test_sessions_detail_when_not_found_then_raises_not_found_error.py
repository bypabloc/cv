"""
Given un session_id inexistente (la query de sesion devuelve None),
When se invoca sessions_service.detail,
Then levanta NotFoundError con code 4040 (AC-11).
"""

from unittest.mock import MagicMock

import pytest
import services.sessions_service as sessions_service
from services._errors import NotFoundError


def test_sessions_detail_when_not_found_then_raises_not_found_error(mocker):
    # Arrange: la query de sesion devuelve None.
    session = MagicMock(name='SQLAlchemySession')
    session_proxy = MagicMock(name='SessionProxy')
    session_proxy.first.return_value = None
    session.execute.return_value = session_proxy
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(sessions_service, 'db_session', return_value=cm)

    # Act + Assert
    with pytest.raises(NotFoundError) as exc_info:
        sessions_service.detail(session_id='nope')

    assert exc_info.value.code == 4040
    assert exc_info.value.error_code == 'NOT_FOUND'
