"""Reorden por botones move-up en /cv/experiences (niche generic) + restore.

Doc 12 (`test_cv_reorder_ui_flow`): 3 experiencias sinteticas creadas via
API (priorities 1/2/3 en generic), seleccion del niche en la UI, snapshot
del orden DOM completo, dos clicks de `cv-entity-move-up` sobre la
sintetica del fondo asserteando el orden DEFINITIVO tras cada mutacion
(la UI refetchea tras el reorder), persistencia tras reload + espejo API,
verificacion de que `vibe` no muestra las sinteticas ni cambio su orden,
RESTORE del orden original via API reorder con el snapshot y delete de
las 3. [AC-5]
"""

from __future__ import annotations

from api._cv_admin_flows import CvAdminSession
from api._cv_admin_flows import minimal_experience_payload
from api._cv_admin_flows import slugs_of

from ._cv_ui import card
from ._cv_ui import cv_admin_response
from ._cv_ui import dom_slugs
from ._cv_ui import goto_cv_overview
from ._cv_ui import open_section
from ._cv_ui import reload_section
from ._cv_ui import select_niche_filter
from ._cv_ui import settle_network
from ._cv_ui import ui_slug
from ._cv_ui import wait_dom_order
from .conftest import CvAdminPage


_REORDER_TIMEOUT = 30_000


def test_cv_reorder_ui_flow(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given 3 experiencias sinteticas (prio 1/2/3 en generic) creadas via API
        y el orden real de dev snapshoteado,
    When la UI filtra por generic y sube DOS veces la sintetica del fondo
        con `cv-entity-move-up`,
    Then el orden DOM refleja cada movimiento, persiste tras reload y en el
        GET API, `vibe` no lista las sinteticas ni cambia su orden, y el
        restore + delete dejan el orden real IDENTICO al pre-test. Cero
        errores de consola.
    """
    page = cv_page.page
    session = cv_admin_session

    # 1. ARRANGE via API: orden real previo + 3 sinteticas (prio 1, 2, 3).
    pre_slugs = slugs_of(session.cv_get('experiences', niche='generic'))
    vibe_pre = slugs_of(session.cv_get('experiences', niche='vibe'))
    synth = [ui_slug(f'reord{i}') for i in (1, 2, 3)]
    for index, slug in enumerate(synth, start=1):
        session.register('experience', slug)
        payload = {
            **minimal_experience_payload(slug),
            'niches': ['generic'],
            'priority': {'generic': index},
        }
        response = session.post('upsert-experience', payload)
        assert response.status == 200, (
            f'[arrange {slug}] HTTP {response.status}: {response.body!r}'
        )

    try:
        # 2. UI: /cv/experiences filtrado por generic — las 3 sinteticas al
        #    final (prioridad desc: synth3, synth2, synth1), el resto
        #    intacto.
        goto_cv_overview(page)
        open_section(page, 'experiences')
        select_niche_filter(page, 'generic')
        snapshot = [*pre_slugs, synth[2], synth[1], synth[0]]
        wait_dom_order(page, snapshot, timeout=_REORDER_TIMEOUT)

        # 3. Snapshot del orden DOM completo (== el esperado).
        assert dom_slugs(page) == snapshot

        # 4. Subir la sintetica del fondo (synth[0]) DOS veces, asserteando
        #    el orden definitivo tras el refetch de cada mutacion.
        after_first = [*pre_slugs, synth[2], synth[0], synth[1]]
        after_second = [*pre_slugs, synth[0], synth[2], synth[1]]
        for expected in (after_first, after_second):
            with page.expect_response(
                cv_admin_response('reorder'),
                timeout=_REORDER_TIMEOUT,
            ):
                card(page, synth[0]).locator(
                    '[data-testid=cv-entity-move-up]',
                ).click()
            wait_dom_order(page, expected, timeout=_REORDER_TIMEOUT)

        # 5. Reload: el orden persiste; el GET API coincide con el DOM.
        reload_section(page)
        select_niche_filter(page, 'generic')
        wait_dom_order(page, after_second, timeout=_REORDER_TIMEOUT)
        api_order = slugs_of(session.cv_get('experiences', niche='generic'))
        assert api_order == after_second

        # 6. Cambiar el selector a vibe: las sinteticas NO aparecen y el
        #    orden de vibe no cambio.
        select_niche_filter(page, 'vibe')
        settle_network(page)
        vibe_dom = dom_slugs(page)
        assert [s for s in vibe_dom if s in set(synth)] == []
        assert vibe_dom == vibe_pre

        # 7. RESTORE: el orden original (snapshot) via API reorder.
        restore = session.post(
            'reorder',
            {
                'entity_type': 'experience',
                'niche': 'generic',
                'ordered_slugs': snapshot,
            },
        )
        assert restore.status == 200, (
            f'[restore] HTTP {restore.status}: {restore.body!r}'
        )
        select_niche_filter(page, 'generic')
        wait_dom_order(page, snapshot, timeout=_REORDER_TIMEOUT)
        assert dom_slugs(page) == snapshot
    finally:
        # Teardown: borrar las 3 sinteticas (idempotente; tambien quedan
        # registradas en el teardown de sesion).
        for slug in synth:
            session.post(
                'delete-experience',
                {'slug': slug},
                retries=3,
                delay=2.0,
            )

    # El orden real de dev quedo identico al pre-test.
    final = slugs_of(session.cv_get('experiences', niche='generic'))
    assert final == pre_slugs
    assert cv_page.console_errors == []
