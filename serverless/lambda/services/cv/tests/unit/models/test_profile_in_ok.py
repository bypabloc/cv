"""ProfileIn acepta el shape del seed profile.ts (contacts + stats).

Given el payload del profile singleton,
When se valida con ProfileIn y se dumpea by_alias sin _meta,
Then contacts/stats/avatarUrl conservan el shape del seed.
"""


def test_profile_in_ok():
    from models.content import ProfileIn

    payload = {
        'name': 'Pablo Contreras',
        'handle': 'bypabloc',
        'headline': {'es': 'Titular', 'en': 'Headline'},
        'summary': {'es': 'Resumen', 'en': 'Summary'},
        'location': 'Lima, Peru',
        'availability': {'es': 'Remoto'},
        'contacts': {
            'email': 'user@example.com',
            'phone': '+51 900000000',
            'linkedin': 'https://linkedin.com/in/example',
            'github': 'https://github.com/example',
            'website': 'https://example.com',
        },
        'avatarUrl': 'https://cdn.example.com/avatar.avif',
        'niches': ['generic'],
        'stats': {
            'yearsExperience': 12,
            'companies': 8,
            'countries': 4,
            'certifications': 11,
        },
        '_meta': {'ip': '203.0.113.10'},
    }

    model = ProfileIn.model_validate(payload)
    dumped = model.model_dump(
        by_alias=True, exclude_none=True, exclude={'meta'},
    )

    assert dumped['handle'] == 'bypabloc'
    assert dumped['avatarUrl'] == 'https://cdn.example.com/avatar.avif'
    assert dumped['contacts'] == {
        'email': 'user@example.com',
        'phone': '+51 900000000',
        'linkedin': 'https://linkedin.com/in/example',
        'github': 'https://github.com/example',
        'website': 'https://example.com',
    }
    assert dumped['stats'] == {
        'yearsExperience': 12,
        'companies': 8,
        'countries': 4,
        'certifications': 11,
    }
