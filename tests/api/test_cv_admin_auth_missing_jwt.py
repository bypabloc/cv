"""E2E: POST /cv-admin SIN header Authorization -> 401 exacto.

Cubre las DOS operations (content y publish): el 401 sale de
`require_active_user` ANTES de tocar el rate-limit, el guard admin o el
service — el dispatch NUNCA llega a GitHub. El payload del upsert es
VALIDO (la fase de validacion Pydantic corre antes del auth: un payload
invalido daria 400 y no probaria el 401).
"""

from __future__ import annotations

import pytest
from shared.config import admin_origin
from shared.http import HttpClient

from ._cv_admin_flows import minimal_experience_payload, synthetic_slug


@pytest.mark.api
def test_cv_admin_auth_missing_jwt(
    http: HttpClient,
    env: str,
    lambda_filter: str | None,
) -> None:
    """
    Given el Lambda cv_admin desplegado en dev,
    When se invoca content.upsert-experience Y publish.dispatch sin
    Authorization,
    Then ambas responden 401 con el body exacto del contrato (sin filtrar
    detalles) y nada se escribe ni se dispara. [AC-2]
    """
    if lambda_filter is not None and lambda_filter != 'cv_admin':
        pytest.skip(f'--lambda={lambda_filter}: cv_admin omitido')
    origin = admin_origin(env)
    expected_body = {
        'error': 'Missing Authorization header',
        'code': 'MISSING_AUTHORIZATION',
    }

    # content.upsert-experience (payload valido, sin niches -> no escribe).
    r1 = http.post(
        '/cv-admin',
        body={
            'operation': 'content',
            'action': 'upsert-experience',
            **minimal_experience_payload(synthetic_slug('nojwt')),
        },
        origin=origin,
    )
    assert r1.status == 401
    assert r1.body == expected_body

    # publish.dispatch (no llega a GitHub: 401 antes del service).
    r2 = http.post(
        '/cv-admin',
        body={'operation': 'publish', 'action': 'dispatch'},
        origin=origin,
    )
    assert r2.status == 401
    assert r2.body == expected_body
