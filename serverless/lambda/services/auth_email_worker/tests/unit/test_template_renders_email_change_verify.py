"""Test: render_template renderiza el kind email-change-verify.

Given el kind 'email-change-verify' con new_email, verify_url y
     expires_in_min en data,
When se invoca render_template,
Then el subject es el valor exacto de _SUBJECTS_ES['email-change-verify']
     y el text body contiene la verify_url, el new_email y NO deja
     ningun placeholder sin sustituir (no queda '${' literal).

Plan 03 (gestion de usuarios): plantilla del magic-link al email NUEVO.
"""

import pytest

pytestmark = pytest.mark.unit


def test_template_renders_email_change_verify():
    """email-change-verify sustituye new_email + verify_url sin marcadores."""
    from services.template_service import render_template

    # Arrange
    data = {
        'new_email': 'new@x.com',
        'verify_url': 'https://x/y',
        'expires_in_min': 15,
    }

    # Act
    subject, text_body, html_body = render_template(
        kind='email-change-verify',
        data=data,
    )

    # Assert
    assert subject == 'Confirma tu nuevo email en the-full-stack.com'
    assert 'https://x/y' in text_body
    assert 'new@x.com' in text_body
    assert chr(36) + '{' not in text_body
