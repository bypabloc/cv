"""Cada llms-full.txt de produccion: un idioma, una cabecera y un H1 por articulo."""

from __future__ import annotations

import re

from playwright.sync_api import APIRequestContext
import pytest


_MARK = '<!-- article -->'
_HEADER = (
    'URL: ',
    'Lang: ',
    'Published: ',
    'Updated: ',
    'Author: ',
    'Alternate: ',
)


def _outside_fences(text: str) -> list[str]:
    """Lineas fuera de bloques de codigo (un # de bash no es un encabezado)."""
    lines: list[str] = []
    fence = False
    for line in text.split('\n'):
        if re.match(r'^\s*(```|~~~)', line):
            fence = not fence
        elif not fence:
            lines.append(line)
    return lines


@pytest.mark.production
@pytest.mark.parametrize(
    'path,lang', [('/llms-full.txt', 'es'), ('/en/llms-full.txt', 'en')]
)
def test_post_llms_full_has_one_header_and_one_h1_per_article(
    http: APIRequestContext,
    guides: list[dict[str, str]],
    path: str,
    lang: str,
) -> None:
    """
    Given el llms-full.txt publicado de un idioma,
    When se descarga y se separa por la marca de articulo,
    Then hay un articulo por guia de ese idioma, cada uno con la cabecera
    completa y su Lang, exactamente un H1 fuera de los bloques de codigo, y
    ninguna linea de navegacion HTML ([← Indice] o **NN**).
    """
    # Arrange
    expected = len([g for g in guides if ('/en/' in g['md']) == (lang == 'en')])

    # Act
    response = http.get(path)
    articles = response.text().split(_MARK)[1:]
    lines = _outside_fences(response.text())

    # Assert
    assert response.status == 200
    assert len(articles) == expected
    for article in articles:
        head = article.strip().split('\n')[:6]
        assert [h.split(' ', 1)[0] + ' ' for h in head] == list(_HEADER)
        assert head[1] == f'Lang: {lang}'
        assert (
            sum(1 for line in _outside_fences(article) if line.startswith('# '))
            == 1
        )
    assert [
        line for line in lines if re.search(r'\[← (Índice|Index)\]', line)
    ] == []
    assert [
        line for line in lines if re.fullmatch(r'\*\*\d+\*\*', line.strip())
    ] == []
