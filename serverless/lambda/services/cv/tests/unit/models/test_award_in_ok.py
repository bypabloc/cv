"""AwardIn exige title y motivation bilingues.

Given un payload de premio (shape del seed),
When se valida con AwardIn,
Then pasa con title/motivation como bloques bilingues.
"""


def test_award_in_ok():
    from models.content_simple import AwardIn

    payload = {
        'slug': 'innovator-2023',
        'title': {'es': 'Innovador 2023', 'en': 'Innovator 2023'},
        'issuer': 'Destacame',
        'date': '2024-01',
        'url': 'https://example.com/award',
        'motivation': {'es': 'Por liderar', 'en': 'For leading'},
        'niches': ['leader'],
        '_meta': {},
    }

    model = AwardIn.model_validate(payload)
    dumped = model.model_dump(
        by_alias=True, exclude_none=True, exclude={'meta'},
    )

    assert dumped['title'] == {'es': 'Innovador 2023', 'en': 'Innovator 2023'}
    assert dumped['motivation'] == {'es': 'Por liderar', 'en': 'For leading'}
