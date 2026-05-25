"""
Controller example/check.

Orquestador delgado SIN Lambda downstream: arn_config_key vacio. La
logica de negocio vive en services/example_service.py.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from models.example import ExampleCheckModel
from services.example_service import ServiceError
from services.example_service import check_resource
from utils.base_controller import BaseController


class Check(BaseController):
    """
    Controller para la accion 'check' de la operacion 'example'.

    El nombre de la clase es action.capitalize() -> 'Check'.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
    """

    event_model = ExampleCheckModel

    # Sin ARN: esta operacion no invoca ningun Lambda downstream.
    arn_config_key = ''

    def execute(self) -> dict:
        """
        Orquesta example/check: delega al service y normaliza la salida.

        :Authors:
            - <Autor>

        :Created:
            - YYYY-MM-DD
        """
        data = self.validated_data  # instancia de ExampleCheckModel

        try:
            result = check_resource(resource_id=data.resource_id)
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
