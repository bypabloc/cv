"""Flujo completo (10 pasos) de un certificate en /cv/certificates.

Doc 12 (tabla de secciones simples): title, issuer, date, url,
niches+priority. El form de certificate NO tiene campos BiLang (desvio de
la regla "una mutacion es + una en" del doc: se mutan title + url, los dos
campos editables con mas senal). El GET serializa `date` como ISO completo
(`YYYY-MM-DD`), que round-tripea tal cual.
"""

from __future__ import annotations

from api._cv_admin_flows import CvAdminSession

from ._cv_simple_flow import SimpleField
from ._cv_simple_flow import run_simple_section_flow
from ._cv_ui import ui_slug
from .conftest import CvAdminPage


def test_cv_certificate_create_edit_delete_flow(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin real en /cv/certificates,
    When crea un certificate sintetico con todos sus campos, lo reabre, lo
        muta (title + url) y lo elimina,
    Then la hidratacion es exacta, el GET /cv certificates refleja el
        estado final y la lista termina igual al inicio sin errores de
        consola.
    """
    run_simple_section_flow(
        cv_page,
        cv_admin_session,
        section='certificates',
        action_suffix='certificate',
        get_action='certificates',
        slug=ui_slug('cert'),
        fields=[
            SimpleField(
                name='title',
                kind='text',
                create='E2E Cvadm UI Certificate',
                update='E2E Cvadm UI Certificate (updated)',
            ),
            SimpleField(
                name='issuer',
                kind='text',
                create='E2E Cvadm UI Issuer',
            ),
            SimpleField(name='date', kind='text', create='2024-06-15'),
            SimpleField(
                name='url',
                kind='text',
                create='https://example.com/e2e-cvadm-ui-cert',
                update='https://example.com/e2e-cvadm-ui-cert-v2',
            ),
        ],
    )
