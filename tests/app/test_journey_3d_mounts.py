"""Journey 3D monta el canvas y sale del fallback de carga.

Regresion del bug de CSP en prod (2026-07-03): el typesetter de troika
(drei Text) corria en un worker via Blob URL cuyo importScripts() interno
bloqueaba `script-src` -> los <Text> suspendian para siempre y la isla
quedaba pegada en "Cargando el mundo 3D…" con el canvas montado pero
oculto. El fix corre troika en el main thread (configureTextBuilder en
text-font.ts). Este test falla si CUALQUIER suspension permanente vuelve a
dejar la isla en el fallback.
"""

from __future__ import annotations

from collections.abc import Callable

from playwright.sync_api import Page
import pytest
from shared import browser as browser_tools


@pytest.mark.app
def test_journey_home_mounts_3d_and_leaves_loading_fallback(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """La experiencia 3D monta y el fallback "Cargando" desaparece.

    Given journey desplegado en el entorno activo,
    When se carga su home `/` en un browser con WebGL2,
    Then el canvas WebGL queda montado y el texto del fallback de Suspense
    ("Cargando el mundo 3D…") desaparece del body (la app 3D termino de
    suspender: fonts, chunks y escena inicial listos).
    """
    # Arrange
    url = f'{subdomain("journey")}/'

    # Act
    browser_tools.goto(page, url)
    page.wait_for_selector('canvas', state='attached', timeout=30_000)
    page.wait_for_function(
        "() => !document.body.innerText.includes('Cargando el mundo 3D')",
        timeout=30_000,
    )

    # Assert
    assert page.locator('canvas').count() == 1
    assert 'Cargando el mundo 3D' not in page.locator('body').inner_text()
