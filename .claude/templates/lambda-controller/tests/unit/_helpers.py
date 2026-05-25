"""
Helpers compartidos por los tests unitarios.

No expone tests. Los archivos test_*.py de este directorio son cada uno
un caso independiente y comparten estos builders.

El prefijo '_' impide que pytest lo confunda con un archivo de tests.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from typing import Any


def build_event(
    *,
    operation: str = 'example',
    action: str = 'create',
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Construye un evento Lambda valido para el patron operation+action.

    Parameters
    ----------
    operation : str
        Nombre de la operacion (default 'example').
    action : str
        Nombre de la accion (default 'create').
    data : dict[str, Any] | None
        Payload de la operacion. Si es None usa un payload minimo valido.

    Returns
    -------
    dict[str, Any]
        Evento {operation, action, data}.
    """
    if data is None:
        data = {'resource_id': 'R-1', 'amount': 100}
    return {
        'operation': operation,
        'action': action,
        'data': data,
    }
