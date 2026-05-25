"""Controllers cv/* — invocan el service y normalizan {is_valid, data, code}.

Given cada controller de la operacion cv,
When ejecuta su ciclo run() con un service que devuelve data fija,
Then devuelve {is_valid: True, data, code: 0}.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit

# (controller_module, controller_class, service_attr, returns_list).
_CASES = [
    ('controllers.cv.get', 'Get', 'get_full_cv', False),
    ('controllers.cv.profile', 'Profile', 'get_profile', False),
    ('controllers.cv.experiences', 'Experiences', 'list_experiences', True),
    ('controllers.cv.projects', 'Projects', 'list_projects', True),
    ('controllers.cv.certificates', 'Certificates', 'list_certificates', True),
    ('controllers.cv.awards', 'Awards', 'list_awards', True),
    ('controllers.cv.education', 'Education', 'list_education', True),
    ('controllers.cv.languages', 'Languages', 'list_languages', True),
    ('controllers.cv.references', 'References', 'list_references', True),
    ('controllers.cv.skills', 'Skills', 'list_skill_categories', True),
]


@pytest.mark.parametrize(
    ('module_name', 'class_name', 'service_attr', 'returns_list'), _CASES
)
def test_controllers_invoke_service_and_normalize(
    module_name: str,
    class_name: str,
    service_attr: str,
    returns_list: bool,
):
    import importlib

    from models.cv import CvQueryModel

    # Arrange
    module = importlib.import_module(module_name)
    controller_cls = getattr(module, class_name)
    expected = [{'slug': 'x'}] if returns_list else {'slug': 'x'}

    with patch(
        f'services.cv_service.{service_attr}',
        return_value=expected,
    ):
        controller = controller_cls(event={'niche': 'fintech', 'locale': 'es'})
        controller.validated_data = CvQueryModel(niche='fintech', locale='es')

        # Act
        result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
