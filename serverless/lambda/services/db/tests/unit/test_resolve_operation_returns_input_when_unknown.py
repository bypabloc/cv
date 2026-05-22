"""Util import_controller.resolve_operation — operation desconocida.

Given un codename de operacion que no esta en OPERATIONS,
When se invoca resolve_operation,
Then devuelve el mismo codename recibido (para que el import falle luego
     con un error descriptivo).
"""

import pytest

pytestmark = pytest.mark.unit


def test_resolve_operation_returns_input_when_unknown():
    from utils.import_controller import resolve_operation

    # Act
    result = resolve_operation('unknown_operation')

    # Assert
    assert result == 'unknown_operation'
