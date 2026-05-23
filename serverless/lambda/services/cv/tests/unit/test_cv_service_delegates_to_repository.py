"""Service cv_service.

Given una funcion del cv_repository mockeada,
When se invoca cv_service.list_experiences,
Then delega los kwargs (niche, locale) sin transformarlos.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_cv_service_delegates_to_repository():
    from services import cv_service

    # Arrange
    with patch(
        'services.cv_service._list_experiences',
        return_value=[{'slug': 'x', 'company': 'Y'}],
    ) as mock_fn:
        # Act
        result = cv_service.list_experiences(niche='fintech', locale='es')

    # Assert
    assert result == [{'slug': 'x', 'company': 'Y'}]
    mock_fn.assert_called_once_with(niche='fintech', locale='es')


def test_cv_service_get_full_cv_delegates_to_repository():
    from services import cv_service

    expected = {'profile': {}, 'experiences': []}
    with patch(
        'services.cv_service._get_full_cv',
        return_value=expected,
    ):
        result = cv_service.get_full_cv(niche=None, locale='es')

    assert result == expected
