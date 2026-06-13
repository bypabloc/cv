"""LanguageIn exige slug + name/level bilingues.

Given un payload de idioma (el seed deriva el slug del filename; la API
lo exige explicito),
When se valida con LanguageIn,
Then pasa con name/level bilingues.
"""


def test_language_in_ok():
    from models.content_simple import LanguageIn

    payload = {
        'slug': 'english',
        'name': {'es': 'Ingles', 'en': 'English'},
        'level': {'es': 'Intermedio', 'en': 'Intermediate'},
        '_meta': {},
    }

    model = LanguageIn.model_validate(payload)

    assert model.slug == 'english'
    assert model.name.es == 'Ingles'
    assert model.level.en == 'Intermediate'
