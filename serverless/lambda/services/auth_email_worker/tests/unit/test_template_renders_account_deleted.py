"""Test: render_template renderiza el kind account-deleted.

Given el kind 'account-deleted' con data vacio,
When se invoca render_template,
Then el subject es el valor exacto de _SUBJECTS_ES['account-deleted'],
     retorna una 3-tupla y el text body NO esta vacio.

Plan 03 (gestion de usuarios): notificacion de cuenta eliminada.
"""

import pytest

pytestmark = pytest.mark.unit


def test_template_renders_account_deleted():
    """account-deleted retorna 3-tupla con subject exacto y body no vacio."""
    from services.template_service import render_template

    # Arrange
    data: dict[str, object] = {}

    # Act
    result = render_template(kind='account-deleted', data=data)

    # Assert
    assert len(result) == 3
    subject, text_body, html_body = result
    assert subject == 'Tu cuenta fue eliminada'
    assert len(text_body) > 0
