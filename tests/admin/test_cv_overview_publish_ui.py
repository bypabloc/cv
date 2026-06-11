"""Publish UI del overview /cv — INTERCEPTADO (sin dispatch real).

Doc 12 (`test_cv_overview_publish_ui`): el dispatch REAL del workflow lo
cubre la capa API; aqui `POST /cv` con `operation == 'publish'` se
intercepta con `page.route` (patron del modulo app para /track): se
captura el request, se responde 200 LOCAL y se assertan el AlertDialog
(titulo + descripcion + cancelar sin request), el body FLAT exacto del
dispatch con Bearer presente, el toast con el link "Ver en Actions" y el
publish-status re-consultado mostrando `queued` con timestamp.

Desvio del doc 12: la respuesta del dispatch se emula FLAT (el backend
responde el payload del controller al nivel raiz y el api-client la
re-envuelve) y el campo del link es `actions_url`, NO `data.url`.
"""

from __future__ import annotations

import json

from playwright.sync_api import Route

from ._cv_ui import ACTION_TIMEOUT
from ._cv_ui import LOAD_TIMEOUT
from ._cv_ui import goto_cv_overview
from .conftest import CvAdminPage


_FAKE_ACTIONS_URL = (
    'https://github.com/bypabloc/portfolio/actions/runs/999000111'
)
_FAKE_CREATED_AT = '2026-06-10T12:00:00Z'


def test_cv_overview_publish_ui(cv_page: CvAdminPage) -> None:
    """
    Given el overview /cv con `operation=publish` interceptado localmente,
    When cancela el AlertDialog, luego confirma la publicacion,
    Then cancelar NO emite ningun request, confirmar emite EXACTAMENTE
        `{operation:'publish', action:'dispatch'}` con Bearer, aparece el
        toast con el link "Ver en Actions" (href == la URL devuelta) y el
        publish-status muestra `queued` con su timestamp. Cero errores de
        consola.
    """
    # Arrange: interceptor del POST /cv SOLO para operation=publish.
    page = cv_page.page
    dispatched: list[dict[str, object]] = []

    def _handle(route: Route) -> None:
        request = route.request
        body = json.loads(request.post_data or '{}')
        if request.method != 'POST' or body.get('operation') != 'publish':
            route.fallback()
            return
        if body.get('action') == 'dispatch':
            dispatched.append(
                {
                    'body': body,
                    'authorization': request.headers.get(
                        'authorization',
                        '',
                    ),
                },
            )
            payload = {
                'dispatched': True,
                'ref': 'dev',
                'actions_url': _FAKE_ACTIONS_URL,
            }
        else:
            payload = {
                'status': 'queued',
                'ref': 'dev',
                'conclusion': None,
                'created_at': _FAKE_CREATED_AT,
                'url': _FAKE_ACTIONS_URL,
            }
        route.fulfill(
            status=200,
            content_type='application/json',
            body=json.dumps(payload),
        )

    page.route('**/cv', _handle)

    # Act: overview con la publish-card hidratada (status interceptado).
    goto_cv_overview(page)
    page.wait_for_selector(
        '[data-testid=cv-publish-button]',
        timeout=LOAD_TIMEOUT,
    )

    # Act: abrir el dialog y CANCELAR.
    page.click('[data-testid=cv-publish-button]')
    page.wait_for_selector(
        '[data-testid=cv-publish-confirm]',
        timeout=ACTION_TIMEOUT,
    )

    # Assert: titulo + descripcion del AlertDialog (avisa el deploy).
    assert page.get_by_text('Publicar el CV').is_visible() is True
    description = page.inner_text('[role=alertdialog]')
    assert ('deploy de las 6 apps del entorno' in description) is True

    page.click('[data-testid=cv-publish-cancel]')
    page.wait_for_selector(
        '[data-testid=cv-publish-confirm]',
        state='hidden',
        timeout=ACTION_TIMEOUT,
    )
    # Cancelar NO emitio ningun dispatch.
    assert dispatched == []

    # Act: publicar de verdad (interceptado).
    page.click('[data-testid=cv-publish-button]')
    page.wait_for_selector(
        '[data-testid=cv-publish-confirm]',
        timeout=ACTION_TIMEOUT,
    )
    page.click('[data-testid=cv-publish-confirm]')

    # Assert: toast de exito + link "Ver en Actions" con el href devuelto.
    page.wait_for_selector('text=Publicacion lanzada', timeout=ACTION_TIMEOUT)
    link_href = page.get_attribute(
        '[data-testid=cv-publish-actions-link]',
        'href',
    )
    assert link_href == _FAKE_ACTIONS_URL

    # Assert: request capturado EXACTO (body FLAT) + Bearer presente.
    assert len(dispatched) == 1
    assert dispatched[0]['body'] == {
        'operation': 'publish',
        'action': 'dispatch',
    }
    authorization = str(dispatched[0]['authorization'])
    assert authorization[:7] == 'Bearer '
    assert len(authorization) > 7

    # Assert: el publish-status (re-consulta interceptada) muestra queued
    # con su timestamp.
    page.wait_for_function(
        """() => {
            const el = document.querySelector(
                '[data-testid=cv-publish-status]',
            );
            return el !== null && el.innerText.includes('queued');
        }""",
        timeout=ACTION_TIMEOUT,
    )
    status_text = page.inner_text('[data-testid=cv-publish-status]')
    assert ('queued' in status_text) is True
    assert (_FAKE_CREATED_AT in status_text) is True

    # Cero errores de consola.
    assert cv_page.console_errors == []
