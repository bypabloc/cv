"""Modelo de validacion del evento Lambda.

Valida la estructura del evento (operation, action, data) y resuelve
el controller correspondiente.
"""

import json
from typing import Any

from pydantic import BaseModel, Field
from utils.import_controller import import_controller


class EventModel(BaseModel):
    """Valida la estructura del evento y resuelve el controller.

    Formato esperado del evento:
        {
            "operation": "<operation>",
            "action": "<action>",
            "data": { ... payload del controller ... }
        }
    """

    controller_info: Any = Field(
        ...,
        description='Resultado de import_controller (controller resuelto).',
    )
    controller_event: dict[str, Any] = Field(
        ...,
        description='Datos (data) preparados para el controller.',
    )
    operation: str = Field(
        ...,
        description='Nombre de la operacion (puede ser alias).',
    )
    action: str = Field(
        ...,
        description='Accion a ejecutar (create, check, ...).',
    )

    model_config = {
        'extra': 'forbid',
        'str_strip_whitespace': True,
        'validate_assignment': True,
    }

    @classmethod
    def validate_event(cls, event: dict[str, Any]) -> 'EventModel':
        """Valida el evento completo y prepara los datos del controller.

        Parameters
        ----------
        event : dict[str, Any]
            Evento completo con operation, action y data.

        Returns
        -------
        EventModel
            Instancia con el controller resuelto.

        Raises
        ------
        ValueError
            Si el evento no es valido o la operacion no existe.
        """
        if not isinstance(event, dict):
            raise ValueError('Event debe ser un objeto JSON valido')

        if 'operation' not in event:
            raise ValueError('No se especifico la operacion a ejecutar')

        if 'data' not in event:
            raise ValueError('Data es requerida')

        operation = event['operation']
        data = event['data']

        if not operation or not isinstance(operation, str):
            raise ValueError('No se especifico la operacion a ejecutar')

        operation_name = operation.strip()

        if not isinstance(data, dict):
            raise ValueError('Data debe ser un objeto JSON valido')

        if 'action' not in event:
            raise ValueError('La accion None no es valida')

        action = event['action']
        if not action or not isinstance(action, str):
            raise ValueError(f'La accion {action} no es valida')

        action_name = action.strip()

        controller_result = import_controller(operation_name, action_name)

        if not controller_result.get('is_valid'):
            error_data = controller_result.get('data', {})
            message = error_data.get(
                'message',
                f"Controller para '{operation_name}/{action_name}' "
                f"no encontrado",
            )
            raise ValueError(
                f"Operacion '{operation_name}/{action_name}' "
                f"no es valida: {message}",
            )

        if 'data' in controller_result:
            controller_result['data']['operation'] = operation_name
            controller_result['data']['action'] = action_name

        return cls(
            controller_info=controller_result,
            controller_event=data,
            operation=operation_name,
            action=action_name,
        )

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Serializacion: devuelve operation, action y data."""
        _ = kwargs
        return {
            'operation': self.operation,
            'action': self.action,
            'data': self.controller_event,
        }

    def model_dump_json(self, **kwargs: Any) -> str:
        """Serializacion JSON del evento."""
        return json.dumps(self.model_dump(**kwargs))
