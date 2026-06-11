"""shared.db.cv_repository.get_full_cv — sesion compartida.

Given las 9 funciones de seccion stubeadas para capturar su kwarg
     `session` y un db_session falso que cuenta aperturas,
When se invoca get_full_cv,
Then db_session se abre EXACTAMENTE una vez y las 9 secciones reciben
     la MISMA Session compartida (antes: 9 sesiones propias).
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
    'list_certificates',
    'list_awards',
    'list_education',
    'list_languages',
    'list_references',
    'list_skill_categories',
)


def test_cv_repository_get_full_cv_shares_one_session(monkeypatch) -> None:
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
            return {} if _name == 'get_profile' else []

        monkeypatch.setattr(cv_repository, name, _stub)

    # Act
    result = cv_repository.get_full_cv(niche='fintech', locale='es')

    # Assert
    assert opened == [sentinel_session]
    assert received == dict.fromkeys(_SECTION_FUNCS, sentinel_session)
    assert result == {
        'profile': {},
        'experiences': [],
        'projects': [],
        'certificates': [],
        'awards': [],
        'education': [],
        'languages': [],
        'references': [],
        'skillCategories': [],
    }
