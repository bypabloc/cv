"""E2E del action `content.catalogs` del Lambda cv_admin.

`catalogs {}` devuelve los 3 vocabularios para los selects del admin:
`niches` (los 5 slugs en el ORDEN REAL de `display_order` — verificado
consultando Neon, sin inventar), `skills` y `techTags` (listas
`{slug, name}` ordenadas por slug, identicas al contenido real de
`cv_skills` / `tax_tech_tags`).
"""

from __future__ import annotations

import pytest
from shared.environment import Environment

from ._cv_admin_flows import NICHES_DISPLAY_ORDER
from ._cv_admin_flows import CvAdminSession


@pytest.mark.api
def test_cv_admin_catalogs(
    cv_admin_session: CvAdminSession,
    environment: Environment,
) -> None:
    """
    Given una sesion admin sintetica contra cv_admin en dev,
    When invoca content.catalogs,
    Then `niches` es EXACTAMENTE la lista de tax_niches en display_order
    (consultada en Neon) y `skills`/`techTags` replican los vocabularios
    reales `{slug, name}` ordenados por slug. [AC-1]
    """
    # Act
    r = cv_admin_session.post('catalogs', {})

    # Assert
    assert r.status == 200, f'catalogs fallo: HTTP {r.status}: {r.body!r}'
    assert sorted(r.body.keys()) == ['niches', 'skills', 'techTags']

    # niches: el orden REAL del catalogo (Neon) — y coincide con el orden
    # canonico de presentacion del backend (cv_write.NICHES).
    neon_niches = environment.niche_slugs_display_order()
    assert r.body['niches'] == neon_niches
    assert r.body['niches'] == list(NICHES_DISPLAY_ORDER)

    # skills / techTags: shape {slug, name} + contenido EXACTO de los
    # vocabularios reales, ordenados por slug.
    expected_skills = [
        {'slug': slug, 'name': name}
        for slug, name in environment.cv_vocab_rows('cv_skills')
    ]
    assert r.body['skills'] == expected_skills
    assert sorted(r.body['skills'][0].keys()) == ['name', 'slug']

    expected_tags = [
        {'slug': slug, 'name': name}
        for slug, name in environment.cv_vocab_rows('tax_tech_tags')
    ]
    assert r.body['techTags'] == expected_tags
    assert sorted(r.body['techTags'][0].keys()) == ['name', 'slug']
