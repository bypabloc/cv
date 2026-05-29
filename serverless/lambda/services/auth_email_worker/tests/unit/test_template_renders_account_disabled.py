"""Test: render_template renderiza el kind account-disabled.

Given el kind 'account-disabled' con reason en data,
When se invoca render_template,
Then el subject es el valor exacto de _SUBJECTS_ES['account-disabled']
     y el text body contiene el reason.

Plan 03 (gestion de usuarios): notificacion de cuenta deshabilitada.
"""

import pytest

pytestmark = pytest.mark.unit


def test_template_renders_account_disabled():
    """account-disabled sustituye el reason en el cuerpo."""
    from services.template_service import render_template

    # Arrange
    data = {'reason': 'spam'}

    # Act
    subject, text_body, html_body = render_template(
        kind='account-disabled',
        data=data,
    )

    # Assert
    assert subject == 'Tu cuenta fue deshabilitada'
    assert 'spam' in text_body
