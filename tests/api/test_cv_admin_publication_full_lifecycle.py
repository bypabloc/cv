"""E2E del lifecycle de `publication` via el Lambda cv_admin (sin GET).

GAP CONOCIDO del plan: el Lambda `cv` NO expone una action GET
`publications`, asi que la verificacion de lectura publica de la
plantilla canonica NO aplica a esta entidad. En su lugar el lifecycle se
verifica via el contrato de escritura:

1. CREATE (upsert) -> 200 `{entity, id}`.
2. UPDATE (re-upsert con title mutado y canonical -> null) -> el MISMO
   `id` (upsert real sobre la misma fila).
3. DELETE -> `{entity, deleted: true}`.
4. DELETE idempotente -> 4404 SLUG_NOT_FOUND exacto.
5. RE-UPSERT post-delete -> 200 con un `id` NUEVO (la fila anterior
   realmente se borro) + delete final de limpieza.

Nota de contrato: el campo del payload es `canonical` (PublicationIn),
NO `canonicalUrl` como nombra el doc 11; `summary` es requerido por el
modelo aunque el doc no lo liste.
"""

from __future__ import annotations

import pytest

from ._cv_admin_flows import CvAdminSession
from ._cv_admin_flows import LifecycleSpec
from ._cv_admin_flows import run_entity_lifecycle
from ._cv_admin_flows import synthetic_slug


@pytest.mark.api
def test_cv_admin_publication_full_lifecycle(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin sintetica contra las operations admin del cv en dev,
    When recorre create/update/delete/idempotencia/re-upsert de una
    publication sintetica,
    Then cada paso responde su contrato exacto; la verificacion GET
    publica no aplica (el Lambda cv no expone publications — gap conocido
    del plan). [AC-1, AC-4]
    """
    session = cv_admin_session
    slug = synthetic_slug('pub')
    create = {
        'slug': slug,
        'title': 'E2E Cvadm Publication',
        'platform': 'dev.to',
        'url': 'https://example.com/e2e-cvadm-pub',
        'canonical': 'https://example.com/e2e-cvadm-pub-canonical',
        'date': '2025-04-01',
        'summary': {
            'es': 'Resumen publicacion es.',
            'en': 'Publication summary en.',
        },
        'niches': ['generic'],
        'priority': {'generic': 1},
    }
    update = {
        **create,
        'title': 'E2E Cvadm Publication (updated)',
        'canonical': None,
    }

    spec = LifecycleSpec(
        action_suffix='publication',
        get_action=None,
        slug=slug,
        create_payload=create,
        update_payload=update,
        niche_in='generic',
        niche_out='fintech',
    )

    created_id = run_entity_lifecycle(session, spec)

    # 5. RE-UPSERT post-delete: misma clave natural, fila NUEVA (id nuevo).
    r3 = session.post('upsert-publication', create)
    assert r3.status == 200, f'[re-upsert] HTTP {r3.status}: {r3.body!r}'
    assert r3.body['entity'] == slug
    assert r3.body['id'] != created_id

    # Limpieza inline (el teardown del conftest re-intenta idempotente).
    rd = session.post('delete-publication', {'slug': slug})
    assert rd.status == 200
    assert rd.body == {'entity': slug, 'deleted': True}
