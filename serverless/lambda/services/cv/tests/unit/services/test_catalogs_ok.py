"""catalogs devuelve niches + skills + techTags para los selects.

Given las 3 queries devuelven filas,
When se invoca catalog_service.catalogs,
Then el shape es {'niches': [slug...], 'skills': [{slug,name}...],
'techTags': [{slug,name}...]}.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_catalogs_ok(monkeypatch):
    from services import catalog_service

    fake_session = MagicMock()
    niches_result = MagicMock()
    niches_result.scalars.return_value.all.return_value = [
        'fintech', 'generic',
    ]
    skills_result = MagicMock()
    skills_result.all.return_value = [('python', 'Python')]
    tech_result = MagicMock()
    tech_result.all.return_value = [('vue', 'Vue')]
    fake_session.execute.side_effect = [
        niches_result, skills_result, tech_result,
    ]
    monkeypatch.setattr(
        catalog_service, 'db_session', lambda: _ctx(fake_session),
    )

    result = catalog_service.catalogs()

    assert result == {
        'niches': ['fintech', 'generic'],
        'skills': [{'slug': 'python', 'name': 'Python'}],
        'techTags': [{'slug': 'vue', 'name': 'Vue'}],
    }
