"""Test: render_template renderiza el kind email-changed.

Given el kind 'email-changed' con new_email en data,
When se invoca render_template,
Then el subject es el valor exacto de _SUBJECTS_ES['email-changed']
     y el text body contiene el new_email.

Plan 03 (gestion de usuarios): notificacion al email VIEJO del cambio.
"""

import pytest

pytestmark = pytest.mark.unit


def test_template_renders_email_changed():
    """email-changed sustituye el new_email en el cuerpo."""
    from services.template_service import render_template

    # Arrange
    data = {'new_email': 'new@x.com'}

    # Act
    subject, text_body, html_body = render_template(
        kind='email-changed',
        data=data,
    )

    # Assert
    assert subject == 'Tu email fue actualizado'
    assert 'new@x.com' in text_body
