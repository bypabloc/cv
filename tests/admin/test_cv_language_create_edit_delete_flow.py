"""Flujo completo (10 pasos) de un language en /cv/languages.

Doc 12 (tabla de secciones simples): name es/en, level es/en, niches.
Mutacion es (level.es) + en (name.en).
"""

from __future__ import annotations

from api._cv_admin_flows import CvAdminSession

from ._cv_simple_flow import SimpleField
from ._cv_simple_flow import run_simple_section_flow
from ._cv_ui import ui_slug
from .conftest import CvAdminPage


def test_cv_language_create_edit_delete_flow(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin real en /cv/languages,
    When crea un language sintetico con todos sus campos, lo reabre, lo
        muta (level.es + name.en) y lo elimina,
    Then la hidratacion es exacta, el GET /cv languages refleja el estado
        final y la lista termina igual al inicio sin errores de consola.
    """
    run_simple_section_flow(
        cv_page,
        cv_admin_session,
        section='languages',
        action_suffix='language',
        get_action='languages',
        slug=ui_slug('lang'),
        fields=[
            SimpleField(
                name='name',
                kind='bilang',
                create=('Idioma UI', 'UI Language'),
                update=('Idioma UI', 'UI Language (updated)'),
            ),
            SimpleField(
                name='level',
                kind='bilang',
                create=('Basico', 'Basic'),
                update=('Intermedio', 'Basic'),
            ),
        ],
    )
