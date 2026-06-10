"""EndorsementIn acepta el shape del seed (relation bilingue).

Given un payload de recomendacion,
When se valida con EndorsementIn,
Then pasa con los valores exactos.
"""


def test_endorsement_in_ok():
    from models.content_simple import EndorsementIn

    payload = {
        'slug': 'alan-vergara',
        'name': 'Alan Vergara Bravo',
        'role': 'Software Architect Developer',
        'relation': {'es': 'Companero de equipo', 'en': 'Teammate'},
        'company': 'Destacame',
        'linkedin': 'https://linkedin.com/in/example',
        '_meta': {},
    }

    model = EndorsementIn.model_validate(payload)

    assert model.slug == 'alan-vergara'
    assert model.company == 'Destacame'
    assert model.relation.en == 'Teammate'
