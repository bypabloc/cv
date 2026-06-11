"""ReorderIn acepta entity_type valido + niche + ordered_slugs.

Given un payload de reorder valido,
When se valida con ReorderIn,
Then pasa con los valores exactos.
"""


def test_reorder_in_ok():
    from models.content_simple import ReorderIn

    payload = {
        'entity_type': 'experience',
        'niche': 'generic',
        'ordered_slugs': ['exp-b', 'exp-a'],
        '_meta': {},
    }

    model = ReorderIn.model_validate(payload)

    assert model.entity_type == 'experience'
    assert model.niche == 'generic'
    assert model.ordered_slugs == ['exp-b', 'exp-a']
