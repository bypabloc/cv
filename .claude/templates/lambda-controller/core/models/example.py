"""
Modelos Pydantic para la operacion 'example'.

Un modelo por accion (create, check, ...). Cada modelo valida el campo
'data' del evento para esa accion.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from pydantic import BaseModel
from pydantic import field_validator


class ExampleCreateModel(BaseModel):
    """
    Valida el payload de example/create.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
    """

    # Campos obligatorios del payload (data del evento).
    resource_id: str
    amount: int

    # extra='forbid' rechaza campos no declarados (mas estricto).
    # extra='allow' los acepta y preserva (util para passthrough).
    model_config = {
        'extra': 'forbid',
    }

    @field_validator('amount')
    @classmethod
    def amount_must_be_positive(cls, value: int) -> int:
        """El monto debe ser estrictamente positivo."""
        if value <= 0:
            raise ValueError('amount debe ser mayor a 0')
        return value


class ExampleCheckModel(BaseModel):
    """
    Valida el payload de example/check.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
    """

    resource_id: str

    model_config = {
        'extra': 'forbid',
    }
