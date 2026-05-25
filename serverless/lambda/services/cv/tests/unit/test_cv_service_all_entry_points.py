"""Service cv_service — cobertura de todos los entry points.

Cada funcion publica del cv_service simplemente delega en cv_repository.
Este test cubre las que no estan cubiertas por test_cv_service_delegates_to_repository.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ('service_fn_name', 'repo_attr', 'kwargs', 'returns_list'),
    [
        ('get_profile', '_get_profile', {'locale': 'es'}, False),
        (
            'list_projects',
            '_list_projects',
            {'niche': 'fintech', 'locale': 'es'},
            True,
        ),
        ('list_certificates', '_list_certificates', {'niche': None}, True),
        (
            'list_awards',
            '_list_awards',
            {'niche': None, 'locale': 'es'},
            True,
        ),
        (
            'list_education',
            '_list_education',
            {'niche': None, 'locale': 'es'},
            True,
        ),
        (
            'list_languages',
            '_list_languages',
            {'niche': None, 'locale': 'es'},
            True,
        ),
        (
            'list_references',
            '_list_references',
            {'niche': None, 'locale': 'es'},
            True,
        ),
        (
            'list_skill_categories',
            '_list_skill_categories',
            {'niche': None, 'locale': 'es'},
            True,
        ),
    ],
)
def test_cv_service_entry_points_delegate(
    service_fn_name, repo_attr, kwargs, returns_list
):
    from services import cv_service

    expected = [{'x': 1}] if returns_list else {'x': 1}
    with patch(
        f'services.cv_service.{repo_attr}',
        return_value=expected,
    ) as mock_fn:
        result = getattr(cv_service, service_fn_name)(**kwargs)

    assert result == expected
    mock_fn.assert_called_once_with(**kwargs)
