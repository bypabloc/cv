"""services.cv_service.get_all_admin — delega en el repository compartido.

Given get_full_cv_admin del cv_repository mockeado con las 10 secciones,
When se invoca cv_service.get_all_admin() (cache transparente del
     conftest: siempre MISS),
Then devuelve el dict del repository tal cual (shape de edicion).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_cv_service_get_all_admin_delegates(monkeypatch):
    from services import cv_service

    payload = {
        'profile': {'name': 'P'},
        'experiences': [],
        'projects': [],
        'skills': [],
        'education': [],
        'certificates': [],
        'awards': [],
        'languages': [],
        'endorsements': [],
        'publications': [{'slug': 'pub-1'}],
    }
    monkeypatch.setattr(
        cv_service, '_get_full_cv_admin', lambda: payload,
    )

    result = cv_service.get_all_admin()

    assert result == payload
