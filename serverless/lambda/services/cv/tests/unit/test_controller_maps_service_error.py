"""Controller cv — manejo de ServiceError.

Given un service que levanta ServiceError,
When el controller ejecuta run(),
Then devuelve {is_valid: False, code, data: {error_code, message}}.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_controller_maps_service_error():
    from controllers.cv.experiences import Experiences
    from models.cv import CvQueryModel
    from services.cv_service import ServiceError

    # Arrange
    err = ServiceError('boom', code=5000, error_code='DB_QUERY_FAILED')

    with patch(
        'services.cv_service.list_experiences',
        side_effect=err,
    ):
        controller = Experiences(event={'locale': 'es'})
        controller.validated_data = CvQueryModel(locale='es')

        # Act
        result = controller.execute()

    # Assert
    assert result == {
        'is_valid': False,
        'data': {'error_code': 'DB_QUERY_FAILED', 'message': 'boom'},
        'code': 5000,
    }
