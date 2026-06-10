"""Flujo completo (10 pasos) de una education en /cv/education.

Doc 12 (tabla de secciones simples): institution, degree es/en,
description es/en, start, end, url, niches+priority. Hidratacion exacta al
reabrir, mutacion es (degree.es) + en (description.en), espejo API, delete
con confirmacion y teardown idempotente.

Nota round-trip: el GET /cv education serializa `start`/`end` como ANO
(`%Y`), por eso los valores del spec usan `YYYY` (un `2018-03` volveria
como `2018` y romperia la hidratacion exacta).
"""

from __future__ import annotations

from api._cv_admin_flows import CvAdminSession

from ._cv_simple_flow import SimpleField
from ._cv_simple_flow import run_simple_section_flow
from ._cv_ui import ui_slug
from .conftest import CvAdminPage


def test_cv_education_create_edit_delete_flow(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin real en /cv/education,
    When crea una education sintetica con todos sus campos, la reabre, la
        muta (degree.es + description.en) y la elimina,
    Then la hidratacion es exacta, el GET /cv education refleja el estado
        final y la lista termina igual al inicio sin errores de consola.
    """
    run_simple_section_flow(
        cv_page,
        cv_admin_session,
        section='education',
        action_suffix='education',
        get_action='education',
        slug=ui_slug('edu'),
        fields=[
            SimpleField(
                name='institution',
                kind='text',
                create='E2E Cvadm UI Institute',
            ),
            SimpleField(name='start', kind='text', create='2019'),
            SimpleField(name='end', kind='text', create='2023'),
            SimpleField(
                name='url',
                kind='text',
                create='https://example.com/e2e-cvadm-ui-edu',
            ),
            SimpleField(
                name='degree',
                kind='bilang',
                create=('Grado UI es', 'UI degree en'),
                update=('Grado UI es (editado)', 'UI degree en'),
            ),
            SimpleField(
                name='description',
                kind='bilang',
                create=('Descripcion edu es.', 'Edu description en.'),
                update=(
                    'Descripcion edu es.',
                    'Edu description en (updated).',
                ),
            ),
        ],
    )
