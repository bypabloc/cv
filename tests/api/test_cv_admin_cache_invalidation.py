"""E2E de la invalidacion del cache por tag 'cv' tras cada escritura.

Las lecturas del Lambda `cv` estan cacheadas en DynamoDB con TTL 900s
(`@cached(tags=['cv'])`). El Lambda cv_admin invalida el tag tras cada
commit: un GET INMEDIATO posterior al upsert/delete debe reflejar el
cambio SIN esperar el TTL. [AC-3]
"""

from __future__ import annotations

import pytest

from ._cv_admin_flows import CvAdminSession
from ._cv_admin_flows import minimal_experience_payload
from ._cv_admin_flows import slugs_of
from ._cv_admin_flows import synthetic_slug


@pytest.mark.api
def test_cv_admin_cache_invalidation(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given el cache del GET /cv experiences poblado (lectura previa),
    When cv_admin upsertea y luego borra una experience sintetica,
    Then el GET INMEDIATO tras cada escritura ya refleja el cambio (la
    invalidacion por tag 'cv' corrio — sin esperar el TTL de 900s).
    [AC-3]
    """
    session = cv_admin_session
    slug = synthetic_slug('cache')
    session.register('experience', slug)

    # 1. GET para poblar el cache; la sintetica aun no existe.
    before = slugs_of(session.cv_get('experiences'))
    assert before.count(slug) == 0

    # 2. upsert -> el GET inmediato YA la incluye.
    payload = {
        **minimal_experience_payload(slug),
        'niches': ['generic'],
        'priority': {'generic': 1},
    }
    r = session.post('upsert-experience', payload)
    assert r.status == 200, f'[upsert] HTTP {r.status}: {r.body!r}'
    after_upsert = slugs_of(session.cv_get('experiences'))
    assert after_upsert.count(slug) == 1

    # 3. delete -> el GET inmediato YA NO la incluye.
    rd = session.post('delete-experience', {'slug': slug})
    assert rd.status == 200, f'[delete] HTTP {rd.status}: {rd.body!r}'
    assert rd.body == {'entity': slug, 'deleted': True}
    after_delete = slugs_of(session.cv_get('experiences'))
    assert after_delete.count(slug) == 0
