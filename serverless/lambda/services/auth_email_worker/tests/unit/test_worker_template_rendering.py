"""Test: template_service.render_template cubre los 5 kinds soportados.

Given cada uno de los 5 kinds de SUPPORTED_KINDS,
When se invoca render_template con un dict de placeholders,
Then retorna (subject, text_body, html_body) NO vacios y los
     placeholders quedaron sustituidos.

Plan 01-auth-infra-basics: las 5 plantillas existen y renderizan
correctamente.
"""

import pytest

pytestmark = pytest.mark.unit


def test_render_template_supports_all_five_kinds():
    """Las 5 plantillas estan presentes y renderizan placeholders."""
    from services.template_service import SUPPORTED_KINDS, render_template

    expected_kinds = (
        'register-magic-link',
        'register-code',
        'login-magic-link',
        'login-code',
        'password-reset',
    )
    assert SUPPORTED_KINDS == expected_kinds

    cases: dict[str, dict[str, object]] = {
        'register-magic-link': {
            'verify_url': 'https://example.com/register/magic?t=abc',
            'expires_in_min': 15,
        },
        'register-code': {
            'code': '7F3KQ29X',
            'expires_in_min': 15,
        },
        'login-magic-link': {
            'verify_url': 'https://example.com/login/magic?t=xyz',
            'expires_in_min': 15,
        },
        'login-code': {
            'code': 'A4PR8KQZ',
            'expires_in_min': 15,
        },
        'password-reset': {
            'verify_url': 'https://example.com/password/reset?t=pqr',
            'expires_in_min': 15,
        },
    }

    expected_subjects = {
        'register-magic-link': 'Activa tu cuenta en the-full-stack.com',
        'register-code': 'Tu codigo de verificacion',
        'login-magic-link': 'Inicia sesion en the-full-stack.com',
        'login-code': 'Tu codigo de acceso',
        'password-reset': 'Restablece tu contrasena',
    }

    for kind in SUPPORTED_KINDS:
        data = cases[kind]
        subject, text_body, html_body = render_template(kind=kind, data=data)

        # Subject correcto
        assert subject == expected_subjects[kind]

        # Cuerpos no vacios
        assert len(text_body) > 0
        assert len(html_body) > 0

        # Placeholders sustituidos: el dict NO debe sobrevivir en bruto
        # como `${verify_url}` o `${code}` en el cuerpo renderizado.
        assert '${verify_url}' not in text_body
        assert '${code}' not in text_body
        assert '${expires_in_min}' not in text_body

        # Y el VALOR de cada placeholder debe aparecer en el texto.
        for value in data.values():
            assert str(value) in text_body
            assert str(value) in html_body


def test_render_template_raises_on_unknown_kind():
    """Un kind fuera de SUPPORTED_KINDS levanta TemplateNotFoundError."""
    from services.template_service import (
        TemplateNotFoundError,
        render_template,
    )

    with pytest.raises(TemplateNotFoundError) as exc_info:
        render_template(kind='unsupported-kind', data={})

    assert 'unknown email kind' in str(exc_info.value)
