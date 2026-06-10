"""Flujo completo (10 pasos) de un award en /cv/awards.

Doc 12 (tabla de secciones simples): issuer, date, url, title es/en,
motivation es/en, niches+priority. Mutacion es (title.es) + en
(motivation.en). El GET serializa `date` como `YYYY-MM` (round-trip-safe
con ese formato).
"""

from __future__ import annotations

from api._cv_admin_flows import CvAdminSession

from ._cv_simple_flow import SimpleField
from ._cv_simple_flow import run_simple_section_flow
from ._cv_ui import ui_slug
from .conftest import CvAdminPage


def test_cv_award_create_edit_delete_flow(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin real en /cv/awards,
    When crea un award sintetico con todos sus campos, lo reabre, lo muta
        (title.es + motivation.en) y lo elimina,
    Then la hidratacion es exacta, el GET /cv awards refleja el estado
        final y la lista termina igual al inicio sin errores de consola.
    """
    run_simple_section_flow(
        cv_page,
        cv_admin_session,
        section='awards',
        action_suffix='award',
        get_action='awards',
        slug=ui_slug('award'),
        fields=[
            SimpleField(
                name='title',
                kind='bilang',
                create=('Premio UI es', 'UI award en'),
                update=('Premio UI es (editado)', 'UI award en'),
            ),
            SimpleField(
                name='issuer',
                kind='text',
                create='E2E Cvadm UI Org',
            ),
            SimpleField(name='date', kind='text', create='2023-11'),
            SimpleField(
                name='url',
                kind='text',
                create='https://example.com/e2e-cvadm-ui-award',
            ),
            SimpleField(
                name='motivation',
                kind='bilang',
                create=('Motivacion UI es.', 'UI motivation en.'),
                update=('Motivacion UI es.', 'UI motivation en (updated).'),
            ),
        ],
    )
