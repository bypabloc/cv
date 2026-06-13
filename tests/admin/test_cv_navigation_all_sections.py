"""Navegacion completa del editor CV: overview + las 10 sub-rutas.

Doc 12 (`test_cv_navigation_all_sections`): login admin real -> /cv ->
las 10 cards del overview con su conteo == la fuente de datos de cada
seccion (GET /cv publico; publications via content.get-all admin, su
unica lectura) -> publish-card visible con boton habilitado -> cada
sub-ruta renderiza su lista (N items == la fuente), marca la seccion
activa en el sub-nav y no deja skeleton residual tras networkidle.
Cierra con cero errores de consola acumulados en TODO el recorrido.
"""

from __future__ import annotations

from api._cv_admin_flows import CvAdminSession

from ._cv_ui import LOAD_TIMEOUT
from ._cv_ui import cards_count
from ._cv_ui import goto_cv_overview
from ._cv_ui import settle_network
from .conftest import CvAdminPage


# Seccion del admin -> action del GET /cv publico (None = sin lectura
# publica: publications se lee del content.get-all admin).
_READ_ACTIONS: dict[str, str | None] = {
    'profile': 'profile',
    'experiences': 'experiences',
    'projects': 'projects',
    'education': 'education',
    'certificates': 'certificates',
    'awards': 'awards',
    'languages': 'languages',
    'endorsements': 'references',
    'publications': None,
    'skills': 'skills',
}


def _expected_count(session: CvAdminSession, section: str) -> int | None:
    """Conteo esperado de la card del overview de cada seccion."""
    action = _READ_ACTIONS[section]
    if action is None:
        # publications: la UI (overview y sub-ruta) lee del get-all
        # admin — misma fuente aqui.
        r = session.post('get-all', {})
        assert r.status == 200
        return len(r.body['publications'])
    data = session.cv_get(action)
    if section == 'profile':
        return 1 if isinstance(data, dict) and len(data) > 0 else 0
    return len(data)


def test_cv_navigation_all_sections(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin real (whitelisted) en el shell del admin de dev,
    When navega a /cv y recorre las 10 sub-rutas del editor CV,
    Then el overview muestra las 10 cards con el conteo exacto del GET /cv,
        la publish-card con su boton habilitado, cada sub-ruta lista N items
        == al GET correspondiente con su item del sub-nav activo y sin
        skeleton residual, y no se acumula NINGUN error de consola.
    """
    # Arrange: conteos esperados via API (misma fuente que la UI).
    page = cv_page.page
    expected = {
        section: _expected_count(cv_admin_session, section)
        for section in _READ_ACTIONS
    }

    # Act: overview.
    goto_cv_overview(page)

    # Assert: 10 cards con su conteo exacto (espera el conteo hidratado).
    for section, count in expected.items():
        card_selector = f'[data-testid=cv-section-card-{section}]'
        page.wait_for_selector(card_selector, timeout=LOAD_TIMEOUT)
        count_selector = f'[data-testid=cv-section-count-{section}]'
        page.wait_for_selector(count_selector, timeout=LOAD_TIMEOUT)
        shown = page.inner_text(count_selector)
        wanted = '—' if count is None else str(count)
        assert shown == wanted, f'overview {section}: {shown!r} != {wanted!r}'

    # Assert: publish-card visible + boton habilitado.
    page.wait_for_selector(
        '[data-testid=cv-publish-card]',
        timeout=LOAD_TIMEOUT,
    )
    assert page.locator('[data-testid=cv-publish-button]').is_enabled() is True

    # Act + Assert: cada sub-ruta (10) via el sub-nav.
    for section, count in expected.items():
        page.click(f'[data-testid=cv-subnav-{section}]')
        page.wait_for_url(f'**/cv/{section}/**', timeout=LOAD_TIMEOUT)
        # El item activo del sub-nav lleva la clase de acento.
        active_class = page.get_attribute(
            f'[data-testid=cv-subnav-{section}]',
            'class',
        )
        assert ('bg-accent' in (active_class or '')) is True
        if section == 'profile':
            page.wait_for_selector(
                '[data-testid=cv-profile-skeleton]',
                state='detached',
                timeout=LOAD_TIMEOUT,
            )
            page.wait_for_selector(
                '[data-testid=cv-field-name]',
                timeout=LOAD_TIMEOUT,
            )
        else:
            page.wait_for_selector(
                '[data-testid=cv-entity-new]',
                timeout=LOAD_TIMEOUT,
            )
            page.wait_for_selector(
                '[data-testid=cv-section-skeleton]',
                state='detached',
                timeout=LOAD_TIMEOUT,
            )
            settle_network(page)
            wanted_cards = 0 if count is None else count
            got_cards = cards_count(page)
            assert got_cards == wanted_cards, (
                f'{section}: {got_cards} cards != {wanted_cards}'
            )
        # Sin skeleton residual tras networkidle.
        settle_network(page)
        assert page.locator('[data-testid=cv-section-skeleton]').count() == 0
        assert page.locator('[data-testid=cv-profile-skeleton]').count() == 0

    # Assert final: cero errores de consola en todo el recorrido.
    assert cv_page.console_errors == []
