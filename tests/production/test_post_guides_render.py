"""Cada guia de produccion renderiza su titulo, su indice y anclas validas."""

from __future__ import annotations

from playwright.sync_api import Page
import pytest


@pytest.mark.production
def test_post_guides_render_title_toc_and_valid_anchors(
    page: Page,
    guides: list[dict[str, str]],
) -> None:
    """
    Given cada guia publicada en llms.txt (es y en),
    When se abre su pagina HTML en produccion,
    Then responde 200, el h1 es el titulo del indice, el TOC tiene 13
    entradas (introduccion + 12 capitulos) y todo link interno #ancla apunta
    a un id que existe en la pagina.
    """
    # Arrange
    problems: list[str] = []

    for guide in guides:
        # Act
        response = page.goto(guide['html'], wait_until='domcontentloaded')
        h1 = page.locator('h1').first.inner_text().strip()
        toc = page.locator('nav.toc li').count()
        broken = page.evaluate(
            """() => [...document.querySelectorAll('a[href^="#"]')]
                .map(a => a.getAttribute('href').slice(1))
                .filter(id => id && !document.getElementById(id))""",
        )

        # Assert (acumulado: un reporte con todas las guias que fallan)
        if response is None or response.status != 200:
            problems.append(
                f'{guide["html"]}: status {response.status if response else None}'
            )
        if h1 != guide['title']:
            problems.append(f'{guide["html"]}: h1 {h1!r}')
        if toc != 13:
            problems.append(f'{guide["html"]}: toc {toc}')
        if broken:
            problems.append(
                f'{guide["html"]}: anclas rotas {sorted(set(broken))}'
            )

    assert guides != []
    assert problems == []
