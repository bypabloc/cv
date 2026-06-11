"""ExperienceIn acepta el shape YAML del seed y dumpea camelCase.

Given un payload valido de experiencia (shape del seed),
When se valida con ExperienceIn y se dumpea by_alias sin _meta,
Then el dict resultante espeja el shape camelCase del seed.
"""


def test_experience_in_ok():
    from models.content import ExperienceIn

    payload = {
        'slug': 'smoke-exp',
        'role': {'es': 'Dev de prueba', 'en': 'Smoke Dev'},
        'company': 'Smoke Corp',
        'country': 'Chile',
        'companyUrl': 'https://smoke.example.com',
        'start': '2024-01',
        'end': '2024-06',
        'seniority': 'senior',
        'metricsEstimated': True,
        'responsibilities': {'es': ['R1'], 'en': ['R1 en']},
        'achievements': {'es': ['A1'], 'en': []},
        'skillsTechnical': ['Python'],
        'skillsSoft': ['Comunicacion'],
        'niches': ['generic'],
        'priority': {'generic': 10},
        '_meta': {'ip': '203.0.113.10'},
    }

    model = ExperienceIn.model_validate(payload)
    dumped = model.model_dump(
        by_alias=True, exclude_none=True, exclude={'meta'},
    )

    assert dumped == {
        'slug': 'smoke-exp',
        'role': {'es': 'Dev de prueba', 'en': 'Smoke Dev'},
        'company': 'Smoke Corp',
        'country': 'Chile',
        'companyUrl': 'https://smoke.example.com',
        'start': '2024-01',
        'end': '2024-06',
        'seniority': 'senior',
        'metricsEstimated': True,
        'responsibilities': {'es': ['R1'], 'en': ['R1 en']},
        'achievements': {'es': ['A1'], 'en': []},
        'skillsTechnical': ['Python'],
        'skillsSoft': ['Comunicacion'],
        'niches': ['generic'],
        'priority': {'generic': 10},
    }
