"""Screenshots multi-viewport de las 6 apps + check de overflow (AC-3).

Porta `tests/feature/smoke/cv-screenshots.spec.ts`: por cada viewport
(mobile 375x812, tablet 768x1024, desktop 1280x800) y cada una de las 6
apps, navega al home, verifica que el hero (`h1`) renderiza sin scroll
horizontal y captura 3 PNG (hero/mid/bottom) en
`tests/results/<niche>/<viewport>/`.

Es lento (~54 PNG: 6 apps x 3 viewports x 3 capturas) -> corre solo en
chromium. Marcado con `screenshots` para poder excluirlo
(`-m 'not screenshots'`) en corridas rapidas. La salida vive en
`tests/results/` (gitignored).
"""

from __future__ import annotations

from collections.abc import Callable
import os

from playwright.sync_api import Browser
import pytest
from shared import browser as browser_tools


_NICHES = ('generic', 'hub', 'fintech', 'architect', 'leader', 'vibe')
_VIEWPORTS = (
    ('mobile', 375, 812),
    ('tablet', 768, 1024),
    ('desktop', 1280, 800),
)

# Directorio de salida: tests/results/ (tests/ es el padre de app/).
_RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'results',
)


@pytest.mark.app
@pytest.mark.screenshots
@pytest.mark.parametrize('viewport', _VIEWPORTS, ids=lambda v: v[0])
@pytest.mark.parametrize('niche', _NICHES)
def test_screenshots_capture_three_views_no_horizontal_overflow(
    browser: Browser,
    subdomain: Callable[[str], str],
    niche: str,
    viewport: tuple[str, int, int],
) -> None:
    """Captura hero/mid/bottom de `{niche}` en cada viewport sin overflow.

    Given el home de `{niche}` desplegado en el viewport `{viewport}`,
    When se carga la pagina y se hace scroll en 3 posiciones,
    Then el `h1` es visible, no hay scroll horizontal
    (`scrollWidth <= clientWidth + 1`) y se escriben 3 PNG en
    `tests/results/<niche>/<viewport>/`.
    """
    # Arrange
    vp_name, width, height = viewport
    out_dir = os.path.join(_RESULTS_DIR, niche, vp_name)
    os.makedirs(out_dir, exist_ok=True)
    context = browser.new_context(
        viewport={'width': width, 'height': height},
    )
    page = context.new_page()
    try:
        # Act: cargar el home y validar el hero
        browser_tools.goto(page, f'{subdomain(niche)}/')
        browser_tools.wait_selector(page, 'h1', state='visible')

        scroll_info = page.evaluate(
            '() => ({'
            ' scrollWidth: document.documentElement.scrollWidth,'
            ' clientWidth: document.documentElement.clientWidth,'
            '})',
        )

        # capturar hero (top)
        browser_tools.screenshot(
            page,
            os.path.join(out_dir, '01-hero.png'),
        )

        # scroll a 150% del viewport (mid) y capturar
        page.evaluate(
            '() => window.scrollTo('
            '{ top: window.innerHeight * 1.5, behavior: "instant" })',
        )
        page.wait_for_timeout(600)
        browser_tools.screenshot(
            page,
            os.path.join(out_dir, '02-mid.png'),
        )

        # scroll al final (bottom) y capturar
        page.evaluate(
            '() => window.scrollTo('
            '{ top: document.body.scrollHeight, behavior: "instant" })',
        )
        page.wait_for_timeout(600)
        browser_tools.screenshot(
            page,
            os.path.join(out_dir, '03-bottom.png'),
        )

        # Assert
        assert page.locator('h1').first.is_visible() is True
        assert int(scroll_info['scrollWidth']) <= (
            int(scroll_info['clientWidth']) + 1
        )
        assert os.path.isfile(os.path.join(out_dir, '01-hero.png')) is True
        assert os.path.isfile(os.path.join(out_dir, '02-mid.png')) is True
        assert os.path.isfile(os.path.join(out_dir, '03-bottom.png')) is True
    finally:
        page.close()
        context.close()
