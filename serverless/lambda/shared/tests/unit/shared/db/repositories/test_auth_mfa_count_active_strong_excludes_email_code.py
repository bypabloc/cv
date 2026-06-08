"""
Given un user con metodos MFA (incluido email_code) y passkeys,
When se llama count_active_strong_mfa,
Then suma TOTP confirmado + passkeys pero EXCLUYE email_code (la query de
  metodos lleva el filtro kind != EMAIL_CODE), a diferencia de count_active_mfa
  que SI cuenta email_code.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_mfa import count_active_strong_mfa

pytestmark = pytest.mark.unit


def test_count_active_strong_mfa_sums_methods_and_passkeys():
    # Arrange: 1 metodo fuerte (TOTP) + 2 passkeys -> session.scalar 2 veces.
    session = MagicMock()
    session.scalar.side_effect = [1, 2]

    # Act
    total = count_active_strong_mfa(session, user_id='u1')

    # Assert
    assert total == 3
    assert session.scalar.call_count == 2


def test_count_active_strong_mfa_methods_query_excludes_email_code():
    # Arrange: capturar el SELECT de metodos (1ra llamada a session.scalar) y
    # confirmar que su WHERE compila el filtro kind != email_code.
    session = MagicMock()
    session.scalar.side_effect = [0, 0]

    # Act
    count_active_strong_mfa(session, user_id='u1')

    # Assert: el statement de metodos (1ra llamada) menciona el filtro de kind.
    methods_stmt = session.scalar.call_args_list[0].args[0]
    compiled = str(
        methods_stmt.compile(compile_kwargs={'literal_binds': True}),
    )
    assert 'auth_mfa_methods.kind != ' in compiled
    assert 'email_code' in compiled


def test_count_active_strong_mfa_only_email_code_returns_zero():
    # Arrange: el user solo tiene email_code -> la query de metodos lo excluye
    # -> 0 metodos fuertes; sin passkeys -> total 0.
    session = MagicMock()
    session.scalar.side_effect = [0, 0]

    # Act
    total = count_active_strong_mfa(session, user_id='u1')

    # Assert
    assert total == 0
