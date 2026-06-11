"""shared.db.cv_repository.get_full_cv_admin — shape de edicion + 1 sesion.

Given las 10 funciones de seccion stubeadas (incluida list_publications)
     y un db_session falso que cuenta aperturas,
When se invoca get_full_cv_admin,
Then db_session se abre EXACTAMENTE una vez, las 10 secciones comparten
     la Session y el dict usa las claves del editor del admin
     (`skills`, `endorsements`, `publications`).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import pytest
import shared.db.cv_repository as cv_repository

pytestmark = pytest.mark.unit

_SECTION_FUNCS = (
    'get_profile',
    'list_experiences',
    'list_projects',
    'list_skill_categories',
    'list_education',
    'list_certificates',
    'list_awards',
    'list_languages',
    'list_references',
    'list_publications',
)


def test_cv_repository_get_full_cv_admin_shape_single_session(
    monkeypatch,
) -> None:
    # Arrange
    sentinel_session = object()
    opened: list[object] = []
    received: dict[str, Any] = {}

    @contextmanager
    def _fake_db_session():
        opened.append(sentinel_session)
        yield sentinel_session

    monkeypatch.setattr(cv_repository, 'db_session', _fake_db_session)
    for name in _SECTION_FUNCS:

        def _stub(*, _name: str = name, **kwargs: Any) -> Any:
            received[_name] = kwargs.get('session')
            return {} if _name == 'get_profile' else [{'slug': _name}]

        monkeypatch.setattr(cv_repository, name, _stub)

    # Act
    result = cv_repository.get_full_cv_admin()

    # Assert
    assert opened == [sentinel_session]
    assert received == dict.fromkeys(_SECTION_FUNCS, sentinel_session)
    assert result == {
        'profile': {},
        'experiences': [{'slug': 'list_experiences'}],
        'projects': [{'slug': 'list_projects'}],
        'skills': [{'slug': 'list_skill_categories'}],
        'education': [{'slug': 'list_education'}],
        'certificates': [{'slug': 'list_certificates'}],
        'awards': [{'slug': 'list_awards'}],
        'languages': [{'slug': 'list_languages'}],
        'endorsements': [{'slug': 'list_references'}],
        'publications': [{'slug': 'list_publications'}],
    }
