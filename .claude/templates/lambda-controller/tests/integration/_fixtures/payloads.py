"""
Builders de payloads para los tests de integracion.

No expone tests. El prefijo '_' del directorio _fixtures impide que
pytest recolecte este modulo como archivo de tests.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from typing import Any


def build_create_event(
    *,
    resource_id: str,
    amount: int = 100,
) -> dict[str, Any]:
    """Evento real para invocar la operacion example/create end-to-end."""
    return {
        'operation': 'example',
        'action': 'create',
        'data': {
            'resource_id': resource_id,
            'amount': amount,
        },
    }


def build_check_event(*, resource_id: str) -> dict[str, Any]:
    """Evento real para invocar la operacion example/check end-to-end."""
    return {
        'operation': 'example',
        'action': 'check',
        'data': {'resource_id': resource_id},
    }
