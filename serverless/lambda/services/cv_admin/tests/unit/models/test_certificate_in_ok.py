"""CertificateIn acepta date YYYY-MM-DD y title plano (no bilingue).

Given un payload de certificado (shape del seed),
When se valida con CertificateIn,
Then pasa con los valores exactos.
"""


def test_certificate_in_ok():
    from models.content_simple import CertificateIn

    payload = {
        'slug': 'docker-2023',
        'title': 'Docker — Guia practica',
        'issuer': 'DevTalles',
        'date': '2023-04-20',
        'url': 'https://example.com/cert',
        'niches': ['architect', 'generic'],
        '_meta': {},
    }

    model = CertificateIn.model_validate(payload)

    assert model.slug == 'docker-2023'
    assert model.title == 'Docker — Guia practica'
    assert model.date == '2023-04-20'
    assert model.niches == ['architect', 'generic']
