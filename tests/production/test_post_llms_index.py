"""llms.txt de produccion lista cada guia en es y en y enlaza ambos llms-full."""

from __future__ import annotations

from playwright.sync_api import APIRequestContext
import pytest


@pytest.mark.production
def test_post_llms_index_links_every_guide_and_both_full_files(
    http: APIRequestContext,
    guides: list[dict[str, str]],
) -> None:
    """
    Given el llms.txt publicado de post,
    When se piden llms.txt y cada .md que enlaza,
    Then llms.txt responde 200 como texto, enlaza /llms-full.txt y
    /en/llms-full.txt, lista la misma cantidad de guias en es y en, y cada .md
    responde 200 con text/markdown.
    """
    # Arrange
    response = http.get('/llms.txt')
    body = response.text()
    es = [g for g in guides if '/en/' not in g['md']]
    en = [g for g in guides if '/en/' in g['md']]

    # Act
    md_status = {g['md']: http.get(g['md']) for g in guides}

    # Assert
    assert response.status == 200
    assert response.headers['content-type'].startswith('text/plain')
    assert 'https://post.the-full-stack.com/llms-full.txt' in body
    assert 'https://post.the-full-stack.com/en/llms-full.txt' in body
    assert len(es) == len(en)
    assert [url for url, r in md_status.items() if r.status != 200] == []
    assert [
        url
        for url, r in md_status.items()
        if not r.headers['content-type'].startswith('text/markdown')
    ] == []
