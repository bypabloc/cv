"""E2E: user activo NO whitelisted -> 404 NOT_FOUND (anti-enumeration).

Un access JWT VALIDO de un user que NO esta en la whitelist SSM
`admin-emails` recibe 404 con el MISMO body que una ruta inexistente
(`{'error': 'NOT_FOUND', 'code': 'NOT_FOUND'}`) en las 3 actions
representativas: content.upsert-experience, content.catalogs y
publish.dispatch. Nada se escribe ni se dispara (el guard corre antes
del service). [AC-2]
"""

from __future__ import annotations

import secrets

import pytest
from shared.auth_support import create_active_user_with_password
from shared.auth_support import login_with_password
from shared.config import admin_origin
from shared.environment import Environment
from shared.http import HttpClient

from ._cv_admin_flows import minimal_experience_payload
from ._cv_admin_flows import synthetic_slug


@pytest.mark.api
def test_cv_admin_auth_non_admin_404(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    lambda_filter: str | None,
) -> None:
    """
    Given un user sintetico ACTIVO con access JWT valido pero NO promovido
    a la whitelist admin-emails,
    When invoca content.upsert-experience, content.catalogs y
    publish.dispatch,
    Then las 3 responden 404 con `error == 'NOT_FOUND'` exacto
    (anti-enumeration: mismo body que una ruta inexistente). [AC-2]
    """
    if lambda_filter is not None and lambda_filter != 'cv_admin':
        pytest.skip(f'--lambda={lambda_filter}: cv_admin omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')

    origin = admin_origin(env)
    email = (
        f'success+e2e-cvadm-nonadmin-{secrets.token_hex(3)}'
        '@simulator.amazonses.com'
    )
    try:
        user_id = create_active_user_with_password(
            http,
            environment,
            origin,
            email,
            bypass,
        )
        if not user_id:
            pytest.fail('no se pudo crear el user sintetico no-admin')
        access, _refresh = login_with_password(http, origin, email, bypass)
        if not access:
            pytest.fail('login del user no-admin fallo (sin access token)')

        cases = (
            (
                'content',
                'upsert-experience',
                minimal_experience_payload(synthetic_slug('nonadm')),
            ),
            ('content', 'catalogs', {}),
            ('publish', 'dispatch', {}),
        )
        for operation, action, payload in cases:
            r = http.post(
                '/cv-admin',
                body={'operation': operation, 'action': action, **payload},
                origin=origin,
                bearer=access,
            )
            assert r.status == 404, (
                f'{operation}.{action}: HTTP {r.status}: {r.body!r}'
            )
            assert r.body == {'error': 'NOT_FOUND', 'code': 'NOT_FOUND'}, (
                f'{operation}.{action}: {r.body!r}'
            )
    finally:
        environment.cleanup_users([email])
