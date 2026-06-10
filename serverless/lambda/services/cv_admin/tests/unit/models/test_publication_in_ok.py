"""PublicationIn acepta el shape del seed (summary bilingue + canonical).

Given un payload de publicacion,
When se valida con PublicationIn,
Then pasa con los valores exactos.
"""


def test_publication_in_ok():
    from models.content_simple import PublicationIn

    payload = {
        'slug': 'mi-articulo',
        'title': 'Mi articulo',
        'platform': 'Dev.to',
        'url': 'https://dev.to/example',
        'canonical': 'https://example.com/blog',
        'date': '2026-01-15',
        'summary': {'es': 'Resumen'},
        '_meta': {},
    }

    model = PublicationIn.model_validate(payload)

    assert model.slug == 'mi-articulo'
    assert model.canonical == 'https://example.com/blog'
    assert model.date == '2026-01-15'
