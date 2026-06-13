"""Edicion del profile singleton en /cv/profile — snapshot + restore.

Doc 12 (`test_cv_profile_edit_flow`): el profile es el singleton REAL del
CV de dev — NO se crea uno sintetico. Snapshot API antes de tocar nada,
hidratacion del form contra el snapshot campo a campo, edicion con
marcadores `E2E-CVADM-UI`, persistencia tras reload, RESTORE por UI con
los valores del snapshot y verificacion GET == snapshot. El restore corre
ADEMAS en el `finally` via `upsert-profile` API por si el spec muere a
mitad.
"""

from __future__ import annotations

import secrets

from api._cv_admin_flows import CvAdminSession

from ._cv_ui import bilang_values
from ._cv_ui import field_value
from ._cv_ui import fill_bilang
from ._cv_ui import fill_field
from ._cv_ui import goto_cv_overview
from ._cv_ui import open_profile
from ._cv_ui import save_profile
from ._cv_ui import wait_profile_loaded
from .conftest import CvAdminPage


def _bilang(snapshot: dict, key: str) -> tuple[str, str]:
    """Par (es, en) de un campo BiLang del snapshot ('' si falta)."""
    value = snapshot.get(key) or {}
    return (value.get('es', ''), value.get('en', ''))


def test_cv_profile_edit_flow(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given el profile singleton REAL de dev y su snapshot via GET /cv,
    When el form de /cv/profile se hidrata, se edita con marcadores, se
        recarga y se restaura por UI,
    Then la hidratacion coincide con el snapshot campo a campo, los
        marcadores persisten tras el reload y el GET final es identico al
        snapshot original. Cero errores de consola.
    """
    # 1. SNAPSHOT API: el estado a restaurar (tambien en el finally).
    page = cv_page.page
    session = cv_admin_session
    snapshot = session.cv_get('profile')
    marker = f'E2E-CVADM-UI-{secrets.token_hex(3)}'
    contacts = snapshot.get('contacts') or {}
    stats = snapshot.get('stats') or {}

    try:
        # 2. Form hidratado con los valores actuales (vs snapshot).
        goto_cv_overview(page)
        open_profile(page)
        assert field_value(page, 'cv-field-name') == snapshot['name']
        assert field_value(page, 'cv-field-handle') == snapshot['handle']
        assert bilang_values(page, 'headline') == _bilang(
            snapshot,
            'headline',
        )
        assert bilang_values(page, 'summary') == _bilang(snapshot, 'summary')
        assert field_value(page, 'cv-field-location') == snapshot.get(
            'location',
            '',
        )
        assert field_value(page, 'cv-field-avatarUrl') == snapshot.get(
            'avatarUrl',
            '',
        )
        assert field_value(page, 'cv-field-email') == contacts.get(
            'email',
            '',
        )
        assert field_value(page, 'cv-field-linkedin') == contacts.get(
            'linkedin',
            '',
        )
        assert field_value(page, 'cv-field-github') == contacts.get(
            'github',
            '',
        )
        original_years = int(stats.get('yearsExperience', 0))
        assert field_value(page, 'cv-field-yearsExperience') == str(
            original_years,
        )
        assert field_value(page, 'cv-field-companies') == str(
            stats.get('companies', 0),
        )

        # 3. Editar: headline.es, summary.en, location, stats.years (+1).
        headline = _bilang(snapshot, 'headline')
        summary = _bilang(snapshot, 'summary')
        fill_bilang(page, 'headline', f'{marker} headline es', headline[1])
        fill_bilang(page, 'summary', summary[0], f'{marker} summary en')
        fill_field(page, 'cv-field-location', f'{marker} City')
        fill_field(
            page,
            'cv-field-yearsExperience',
            str(original_years + 1),
        )

        # 4. Guardar -> toast -> reload -> persiste (asserts exactos).
        save_profile(page)
        page.reload(wait_until='load')
        wait_profile_loaded(page)
        assert bilang_values(page, 'headline') == (
            f'{marker} headline es',
            headline[1],
        )
        assert bilang_values(page, 'summary') == (
            summary[0],
            f'{marker} summary en',
        )
        assert field_value(page, 'cv-field-location') == f'{marker} City'
        assert field_value(page, 'cv-field-yearsExperience') == str(
            original_years + 1,
        )

        # 5. RESTORE por UI: re-editar con los valores del snapshot.
        fill_bilang(page, 'headline', headline[0], headline[1])
        fill_bilang(page, 'summary', summary[0], summary[1])
        fill_field(page, 'cv-field-location', snapshot.get('location', ''))
        fill_field(page, 'cv-field-yearsExperience', str(original_years))
        save_profile(page)

        # 6. Verificar restauracion: GET API == snapshot original.
        restored = session.cv_get('profile')
        assert restored['headline'] == snapshot['headline']
        assert restored['summary'] == snapshot['summary']
        assert restored.get('location') == snapshot.get('location')
        assert restored['stats'] == snapshot['stats']
        assert restored['name'] == snapshot['name']
        assert restored['contacts'] == snapshot['contacts']
    finally:
        # Restore de seguridad via API (idempotente) por si el spec murio
        # con los marcadores aplicados.
        response = session.post('upsert-profile', snapshot)
        assert response.status == 200, (
            f'[restore-finally] HTTP {response.status}: {response.body!r} '
            '— el profile REAL de dev pudo quedar con marcadores '
            'E2E-CVADM-UI'
        )

    # El GET final es IDENTICO al snapshot (el CV real de dev intacto).
    assert session.cv_get('profile') == snapshot
    assert cv_page.console_errors == []
