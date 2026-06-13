"""Flujo completo (10 pasos) de una publication en /cv/publications.

Desde el plan d-cv-consolidation publications tiene lectura REAL en el
editor: la sub-ruta y el overview leen del `content.get-all` admin (la
entidad sigue SIN action de lectura en el GET /cv publico, por eso
`get_action=None` — el espejo lo cubre la persistencia tras reload, que
ejercita el get-all de punta a punta). Campos del doc 12: title,
platform, url, canonical opcional, date y summary es/en. Mutacion:
title + summary.en.
"""

from __future__ import annotations

from api._cv_admin_flows import CvAdminSession

from ._cv_simple_flow import SimpleField
from ._cv_simple_flow import run_simple_section_flow
from ._cv_ui import ui_slug
from .conftest import CvAdminPage


def test_cv_publication_create_edit_delete_flow(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin real en /cv/publications,
    When crea una publication sintetica con todos sus campos, la reabre,
        la muta (title + summary.en) y la elimina,
    Then la card aparece/persiste/desaparece via la lectura get-all, la
        hidratacion es exacta campo a campo y la lista termina igual al
        inicio sin errores de consola.
    """
    run_simple_section_flow(
        cv_page,
        cv_admin_session,
        section='publications',
        action_suffix='publication',
        get_action=None,
        slug=ui_slug('pub'),
        fields=[
            SimpleField(
                name='title',
                kind='text',
                create='E2E Cvadm UI Publication',
                update='E2E Cvadm UI Publication (editada)',
            ),
            SimpleField(name='platform', kind='text', create='dev.to'),
            SimpleField(
                name='url',
                kind='text',
                create='https://example.com/e2e-cvadm-ui-pub',
            ),
            SimpleField(
                name='canonical',
                kind='text',
                create='https://example.com/e2e-cvadm-ui-pub-canonical',
            ),
            SimpleField(name='date', kind='text', create='2026-01-15'),
            SimpleField(
                name='summary',
                kind='bilang',
                create=('Resumen pub es.', 'Pub summary en.'),
                update=('Resumen pub es.', 'Pub summary en (updated).'),
            ),
        ],
    )
