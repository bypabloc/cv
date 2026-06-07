"""Los modelos aceptan `_meta` como input y lo exponen como `.meta`.

Given un payload con clave `_meta` (alias),
When se valida con LoginCheckEmailIn,
Then la instancia expone el campo como `.meta` y conserva la metadata.
"""


def test_login_check_email_in_accepts_meta_alias():
    from models.login import LoginCheckEmailIn

    payload = {
        'email': 'visitor@example.com',
        'cf_turnstile_response': 'token-xxx',
        '_meta': {
            'ip': '203.0.113.10',
            'country': 'CL',
            'user_agent': 'pytest',
            'origin': 'https://admin.portfolio.dev.the-full-stack.com',
        },
    }

    parsed = LoginCheckEmailIn.model_validate(payload)

    assert parsed.email == 'visitor@example.com'
    assert parsed.meta.ip == '203.0.113.10'
    assert parsed.meta.country == 'CL'
    assert parsed.meta.user_agent == 'pytest'
    assert parsed.meta.origin == (
        'https://admin.portfolio.dev.the-full-stack.com'
    )
