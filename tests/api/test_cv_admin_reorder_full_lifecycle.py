"""E2E del lifecycle de `reorder` (experiences, niche generic) — restore.

Toca el ORDEN real de dev, con snapshot + restore obligatorio:

1. PRE: snapshot del orden real de `experiences?niche=generic`.
2. ARRANGE: 3 experiencias sinteticas en generic (priorities 1, 2, 3).
3. SNAPSHOT: orden completo actual (reales + sinteticas al final).
4. REORDER: lista completa moviendo SOLO las sinteticas al final en orden
   invertido — las reales conservan su posicion relativa.
5. VERIFY: GET == el orden enviado, exacto.
6. EDGE: `ordered_slugs` incompleto (falta una sintetica) -> 1101
   REORDER_SLUGS_MISMATCH (HTTP 400) con el faltante exacto en detail.
7. RESTORE: reorder con el orden del snapshot -> GET == snapshot.
8. CLEANUP: delete de las 3 sinteticas -> GET == orden pre-test.

Nota: el reorder reescribe los VALORES de prioridad (escala espaciada
descendente); el contrato restaurable es el ORDEN de los slugs, que es lo
que se asserta.
"""

from __future__ import annotations

import pytest

from ._cv_admin_flows import (
    CvAdminSession,
    minimal_experience_payload,
    slugs_of,
    synthetic_slug,
)


@pytest.mark.api
def test_cv_admin_reorder_full_lifecycle(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given el orden real de experiences en generic + 3 sinteticas (prio
    1/2/3),
    When se reordena la lista completa (sinteticas al final invertidas),
    se valida el edge de lista incompleta, se restaura el orden del
    snapshot y se borran las sinteticas,
    Then cada GET refleja el orden EXACTO esperado y el orden real de dev
    queda identico al pre-test. [AC-5]
    """
    session = cv_admin_session

    # 1. PRE: orden real (sin sinteticas) — el estado a restaurar al final.
    pre_slugs = slugs_of(session.cv_get('experiences', niche='generic'))
    assert [s for s in pre_slugs if s.startswith('e2e-cvadm-')] == []

    # 2. ARRANGE: 3 sinteticas en generic con priorities 1, 2, 3.
    synth = [synthetic_slug(f'reord{i}') for i in (1, 2, 3)]
    for index, slug in enumerate(synth, start=1):
        session.register('experience', slug)
        payload = {
            **minimal_experience_payload(slug),
            'niches': ['generic'],
            'priority': {'generic': index},
        }
        r = session.post('upsert-experience', payload)
        assert r.status == 200, f'[arrange {slug}] {r.status}: {r.body!r}'

    try:
        # 3. SNAPSHOT: orden completo actual. Las reales (prioridad mas
        # alta) primero; las sinteticas al final en orden 3, 2, 1.
        snapshot = slugs_of(session.cv_get('experiences', niche='generic'))
        assert sorted(snapshot) == sorted([*pre_slugs, *synth])
        assert snapshot[: len(pre_slugs)] == pre_slugs
        assert snapshot[len(pre_slugs) :] == [synth[2], synth[1], synth[0]]

        # 4. REORDER: reales en su orden + sinteticas invertidas (1, 2, 3).
        reordered = [*pre_slugs, synth[0], synth[1], synth[2]]
        r = session.post(
            'reorder',
            {
                'entity_type': 'experience',
                'niche': 'generic',
                'ordered_slugs': reordered,
            },
        )
        assert r.status == 200, f'[reorder] HTTP {r.status}: {r.body!r}'
        assert r.body == {
            'entity_type': 'experience',
            'niche': 'generic',
            'reordered': len(reordered),
        }

        # 5. VERIFY: posiciones exactas — reales sin cambio relativo,
        # sinteticas al final en el orden enviado.
        after = slugs_of(session.cv_get('experiences', niche='generic'))
        assert after == reordered

        # 6. EDGE: lista incompleta (falta una sintetica) -> 1101 exacto.
        incomplete = [*pre_slugs, synth[0], synth[1]]
        edge = session.post(
            'reorder',
            {
                'entity_type': 'experience',
                'niche': 'generic',
                'ordered_slugs': incomplete,
            },
        )
        assert edge.status == 400, f'[edge] HTTP {edge.status}: {edge.body!r}'
        assert edge.body == {
            'error_code': 'REORDER_SLUGS_MISMATCH',
            'message': (
                'ordered_slugs no coincide con las entidades del niche: '
                f'faltantes={[synth[2]]} sobrantes=[]'
            ),
            'detail': {'missing': [synth[2]], 'extra': []},
        }
        # El edge NO altero el orden.
        assert slugs_of(
            session.cv_get('experiences', niche='generic'),
        ) == reordered

        # 7. RESTORE: el orden del snapshot.
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
        assert slugs_of(
            session.cv_get('experiences', niche='generic'),
        ) == snapshot
    finally:
        # 8. CLEANUP: borrar las 3 sinteticas (idempotente).
        for slug in synth:
            session.post('delete-experience', {'slug': slug})

    # El orden real de dev quedo identico al pre-test.
    final = slugs_of(session.cv_get('experiences', niche='generic'))
    assert final == pre_slugs
