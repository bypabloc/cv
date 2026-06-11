"""EducationIn acepta start YYYY (string) y description bilingue.

Given un payload de educacion con start '2017' (solo anio),
When se valida con EducationIn,
Then pasa y el dump conserva el string.
"""


def test_education_in_ok():
    from models.content_simple import EducationIn

    payload = {
        'slug': 'udemy',
        'institution': 'Udemy',
        'start': '2017',
        'url': 'https://udemy.com',
        'description': {'es': 'Cursos', 'en': 'Courses'},
        'niches': ['generic'],
        '_meta': {},
    }

    model = EducationIn.model_validate(payload)
    dumped = model.model_dump(
        by_alias=True, exclude_none=True, exclude={'meta'},
    )

    assert dumped['slug'] == 'udemy'
    assert dumped['start'] == '2017'
    assert dumped['description'] == {'es': 'Cursos', 'en': 'Courses'}
