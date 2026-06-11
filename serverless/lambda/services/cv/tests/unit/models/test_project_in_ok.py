"""ProjectIn acepta el shape YAML del seed (case study + metrics + stack).

Given un payload valido de proyecto,
When se valida con ProjectIn y se dumpea by_alias sin _meta,
Then el dict espeja el shape camelCase del seed.
"""


def test_project_in_ok():
    from models.content import ProjectIn

    payload = {
        'slug': 'smoke-proj',
        'name': 'Smoke Project',
        'summary': {'es': 'Resumen', 'en': 'Summary'},
        'description': {'es': 'Desc'},
        'url': 'https://proj.example.com',
        'status': 'active',
        'projectType': 'fintech-platform',
        'isConfidential': True,
        'stack': ['Vue', 'Django'],
        'caseStudy': {'es': 'Caso'},
        'caseStudyDetailed': {
            'problem': {'es': 'P'},
            'process': {'es': 'Pr'},
            'result': {'es': 'R'},
        },
        'metrics': {'market': 'Chile'},
        'niches': ['fintech'],
        'priority': {'fintech': 90},
        '_meta': {'ip': '203.0.113.10'},
    }

    model = ProjectIn.model_validate(payload)
    dumped = model.model_dump(
        by_alias=True, exclude_none=True, exclude={'meta'},
    )

    assert dumped['slug'] == 'smoke-proj'
    assert dumped['projectType'] == 'fintech-platform'
    assert dumped['isConfidential'] is True
    assert dumped['metricsEstimated'] is False
    assert dumped['stack'] == ['Vue', 'Django']
    assert dumped['caseStudy'] == {'es': 'Caso'}
    assert dumped['caseStudyDetailed'] == {
        'problem': {'es': 'P'},
        'process': {'es': 'Pr'},
        'result': {'es': 'R'},
    }
    assert dumped['metrics'] == {'market': 'Chile'}
