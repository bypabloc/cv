"""
Controller example/create.

El controller es un orquestador delgado: toma el payload ya validado,
delega la logica de negocio al service y normaliza el resultado a
{is_valid, data, code}. NO contiene logica de negocio.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from models.example import ExampleCreateModel
from services.example_service import ServiceError
from services.example_service import create_resource
from utils.base_controller import BaseController


class Create(BaseController):
    """
    Controller para la accion 'create' de la operacion 'example'.

    El nombre de la clase DEBE ser action.capitalize(): para la accion
    'create' la clase se llama 'Create'. import_controller la resuelve
    dinamicamente por ese nombre.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
    """

    # Modelo Pydantic que valida el evento (fase validate).
    event_model = ExampleCreateModel

    # Campo de AppConfig con el ARN del Lambda downstream (fase preload).
    # Dejar '' si la operacion no invoca otro Lambda.
    arn_config_key = 'arn_example'

    def execute(self) -> dict:
        """
        Orquesta example/create: delega al service y normaliza la salida.

        Devuelve siempre {is_valid, data, code}:
          - exito  -> {is_valid: True, data: {...}, code: 0}
          - error  -> {is_valid: False, data: {error_code, message},
            code: <ErrorCode>}

        :Authors:
            - <Autor>

        :Created:
            - YYYY-MM-DD
        """
        data = self.validated_data  # instancia de ExampleCreateModel

        try:
            result = create_resource(
                resource_id=data.resource_id,
                amount=data.amount,
                arn=self.arn,
            )
        except ServiceError as exc:
            return {
                'is_valid': False,
                'data': {
                    'error_code': exc.error_code,
                    'message': exc.message,
                },
                'code': exc.code,
            }

        return {
            'is_valid': True,
            'data': result,
            'code': 0,
        }
