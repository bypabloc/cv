"""E2E del lifecycle del `profile` (singleton) via el Lambda cv_admin.

El profile es el singleton REAL del CV de dev — NO se crea uno sintetico.
El test es snapshot/restore obligatorio:

1. SNAPSHOT: GET /cv profile -> respuesta COMPLETA original.
2. UPSERT: headline/summary/availability/location/stats con valores
   marcador `E2E-CVADM-<rand>`.
3. VERIFY: el GET refleja cada marcador (asserts exactos por campo).
4. RESTORE: upsert-profile con el snapshot original COMPLETO.
5. VERIFY RESTORE: GET == snapshot campo a campo (el CV real de dev queda
   intacto). El restore corre TAMBIEN en el `finally` (si el test muere a
   mitad, el profile real se restaura igual).
"""

from __future__ import annotations

import secrets

import pytest

from ._cv_admin_flows import CvAdminSession


@pytest.mark.api
def test_cv_admin_profile_full_lifecycle(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given el profile singleton REAL de dev y una sesion admin sintetica,
    When se upsertea con valores marcador y luego se restaura con el
    snapshot original completo,
    Then el GET refleja cada marcador tras el upsert y vuelve a ser
    IDENTICO al snapshot tras el restore. [AC-1, AC-3, AC-11]
    """
    session = cv_admin_session
    marker = f'E2E-CVADM-{secrets.token_hex(3)}'

    # 1. SNAPSHOT (la respuesta completa original — la fuente del restore).
    snapshot = session.cv_get('profile')
    required_keys = {'name', 'handle', 'headline', 'summary', 'contacts'}
    assert required_keys - set(snapshot.keys()) == set()

    mutated = {
        **snapshot,
        'headline': {'es': f'{marker} headline es', 'en': f'{marker} hl en'},
        'summary': {'es': f'{marker} summary es', 'en': f'{marker} sum en'},
        'availability': {'es': f'{marker} disp es', 'en': f'{marker} av en'},
        'location': f'{marker} City',
        'stats': {
            'yearsExperience': 91,
            'companies': 92,
            'countries': 93,
            'certifications': 94,
        },
    }

    try:
        # 2. UPSERT con los marcadores.
        r = session.post('upsert-profile', mutated)
        assert r.status == 200, f'[upsert] HTTP {r.status}: {r.body!r}'
        assert r.body['entity'] == snapshot['handle']

        # 3. VERIFY: el GET refleja cada marcador.
        got = session.cv_get('profile')
        assert got['headline'] == {
            'es': f'{marker} headline es',
            'en': f'{marker} hl en',
        }
        assert got['summary'] == {
            'es': f'{marker} summary es',
            'en': f'{marker} sum en',
        }
        assert got['availability'] == {
            'es': f'{marker} disp es',
            'en': f'{marker} av en',
        }
        assert got['location'] == f'{marker} City'
        assert got['stats'] == {
            'yearsExperience': 91,
            'companies': 92,
            'countries': 93,
            'certifications': 94,
        }
        # Lo NO mutado se preserva.
        assert got['name'] == snapshot['name']
        assert got['handle'] == snapshot['handle']
        assert got['contacts'] == snapshot['contacts']
        assert got['avatarUrl'] == snapshot['avatarUrl']
        assert got['niches'] == snapshot['niches']
    finally:
        # 4. RESTORE con el snapshot COMPLETO (tambien si el test murio).
        restore = session.post('upsert-profile', snapshot)
        assert restore.status == 200, (
            f'[restore] HTTP {restore.status}: {restore.body!r} — el '
            'profile REAL de dev pudo quedar con marcadores E2E-CVADM'
        )

    # 5. VERIFY RESTORE: GET identico al snapshot (el CV real intacto).
    final = session.cv_get('profile')
    assert final == snapshot
