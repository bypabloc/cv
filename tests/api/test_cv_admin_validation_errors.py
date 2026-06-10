"""E2E de los errores de validacion del Lambda cv_admin (5 casos, doc 11).

Con sesion admin, una sub-asercion por caso (mismo escenario):

1. slug con mayusculas/espacios -> 400 INVALID_REQUEST (Pydantic);
   nada persiste (GET).
2. niche inexistente -> 400 UNKNOWN_NICHE exacto; nada persiste.
3. fecha malformada `2026-13` -> el regex FlexDate la ACEPTA (dos
   digitos) y `coerce_date` revienta dentro de la transaccion ->
   rollback + 500 INTERNAL_ERROR generico; nada persiste. (Looseness
   conocida del contrato: el doc 11 esperaba 1xxx, el comportamiento
   real es el 500 hermetico del http_handler.)
4. action desconocida `upsert-nope` -> 400 INVALID_REQUEST (resolucion
   de operation/action).
5. payload sin `slug` -> 400 INVALID_REQUEST. (El detail del body es el
   generico 'Event validation failed' — el campo faltante NO viaja en la
   respuesta; senalarlo es un gap conocido del contrato.)
"""

from __future__ import annotations

import pytest

from ._cv_admin_flows import (
    CvAdminSession,
    minimal_experience_payload,
    slugs_of,
    synthetic_slug,
)

# Body EXACTO del 400 de validacion Pydantic (fase validate del
# controller): http_handler lo colapsa a INVALID_REQUEST con el detail
# generico del BaseController.
_VALIDATION_400 = {
    'error': 'Validation failed',
    'code': 'INVALID_REQUEST',
    'extra': {
        'detail': {
            'error': 'INVALID_EVENT_DATA',
            'message': 'Event validation failed',
        },
    },
}


@pytest.mark.api
def test_cv_admin_validation_errors(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin sintetica contra cv_admin en dev,
    When envia los 5 payloads invalidos del doc 11,
    Then cada uno responde su error exacto y el GET publico confirma que
    NADA persistio. [AC-1]
    """
    session = cv_admin_session

    # 1. slug con mayusculas/espacios -> 400 Pydantic (SlugStr kebab-case).
    bad_slug = 'Bad Slug E2E'
    r1 = session.post(
        'upsert-experience',
        {**minimal_experience_payload(synthetic_slug('val')), 'slug': bad_slug},
    )
    assert r1.status == 400, f'[slug] HTTP {r1.status}: {r1.body!r}'
    assert r1.body == _VALIDATION_400
    assert slugs_of(session.cv_get('experiences')).count(bad_slug) == 0

    # 2. niche inexistente -> 400 UNKNOWN_NICHE exacto; nada persiste.
    slug2 = synthetic_slug('valniche')
    session.register('experience', slug2)
    r2 = session.post(
        'upsert-experience',
        {
            **minimal_experience_payload(slug2),
            'niches': ['no-such-niche'],
        },
    )
    assert r2.status == 400, f'[niche] HTTP {r2.status}: {r2.body!r}'
    assert r2.body == {
        'error_code': 'UNKNOWN_NICHE',
        'message': "niches desconocidos: ['no-such-niche']",
        'detail': {'unknown_niches': ['no-such-niche']},
    }
    assert slugs_of(session.cv_get('experiences')).count(slug2) == 0

    # 3. fecha malformada 2026-13 -> 500 INTERNAL_ERROR (rollback total).
    slug3 = synthetic_slug('valdate')
    session.register('experience', slug3)
    r3 = session.post(
        'upsert-experience',
        {**minimal_experience_payload(slug3), 'start': '2026-13'},
    )
    assert r3.status == 500, f'[fecha] HTTP {r3.status}: {r3.body!r}'
    assert r3.body == {
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR',
    }
    assert slugs_of(session.cv_get('experiences')).count(slug3) == 0

    # 4. action desconocida -> 400 de resolucion operation/action.
    r4 = session.post(
        'upsert-nope',
        minimal_experience_payload(synthetic_slug('valact')),
    )
    assert r4.status == 400, f'[action] HTTP {r4.status}: {r4.body!r}'
    assert r4.body['code'] == 'INVALID_REQUEST'
    assert r4.body['error'] == 'Validation failed'

    # 5. payload sin slug -> 400 Pydantic.
    no_slug = minimal_experience_payload(synthetic_slug('valnoslug'))
    del no_slug['slug']
    r5 = session.post('upsert-experience', no_slug)
    assert r5.status == 400, f'[sin slug] HTTP {r5.status}: {r5.body!r}'
    assert r5.body == _VALIDATION_400
