"""Flujo completo (10 pasos) de un endorsement en /cv/endorsements.

Doc 12 (tabla de secciones simples): name, role, company, linkedin,
relation es/en, niches. Mutacion es + en sobre el par `relation`. El GET
publico de la seccion es la action `references` (nombre legacy del
endpoint de lectura).
"""

from __future__ import annotations

from api._cv_admin_flows import CvAdminSession

from ._cv_simple_flow import SimpleField
from ._cv_simple_flow import run_simple_section_flow
from ._cv_ui import ui_slug
from .conftest import CvAdminPage


def test_cv_endorsement_create_edit_delete_flow(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin real en /cv/endorsements,
    When crea un endorsement sintetico con todos sus campos, lo reabre, lo
        muta (relation.es + relation.en) y lo elimina,
    Then la hidratacion es exacta, el GET /cv references refleja el estado
        final y la lista termina igual al inicio sin errores de consola.
    """
    run_simple_section_flow(
        cv_page,
        cv_admin_session,
        section='endorsements',
        action_suffix='endorsement',
        get_action='references',
        slug=ui_slug('endo'),
        fields=[
            SimpleField(
                name='name',
                kind='text',
                create='E2E Cvadm UI Peer',
            ),
            SimpleField(
                name='role',
                kind='text',
                create='Tech Lead',
            ),
            SimpleField(
                name='company',
                kind='text',
                create='E2E Cvadm UI Corp',
            ),
            SimpleField(
                name='linkedin',
                kind='text',
                create='https://linkedin.com/in/e2e-cvadm-ui',
            ),
            SimpleField(
                name='relation',
                kind='bilang',
                create=('Colega UI es.', 'UI peer en.'),
                update=(
                    'Colega UI es (editado).',
                    'UI peer en (updated).',
                ),
            ),
        ],
    )
