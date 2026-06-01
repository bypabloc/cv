"""@module shared.lambda_kit.dispatch — nucleo de despacho de controllers.

`run_controller` concentra el patron que se repetia, identico, dentro
del `handler.py` de los 4 Lambdas del backend:

  1. validar el evento sintetico `{operation, action, data}`;
  2. resolver el `controller_class` (via `validate_event` + `OPERATIONS`);
  3. instanciar el controller con el `controller_event`;
  4. ejecutar su ciclo `run()` (`preload -> validate -> execute`).

Lo que NO se unifica vive en cada `handler.py`: traducir el evento
crudo del trigger (HTTP de API Gateway, `{command, args}`, DynamoDB
Streams) al contrato `{operation, action, data}`, y formatear la
respuesta especifica del trigger. `run_controller` es el pegamento del
medio, generico.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.lambda_kit.validation.event import EventModelClass, validate_event


@dataclass
class DispatchResult:
    """Resultado de `run_controller`.

    Attributes
    ----------
    is_valid : bool
        True si el controller ejecuto y devolvio `is_valid: True`.
    data : dict[str, Any]
        El `data` del resultado del controller (en exito) o del error.
    code : int
        Codigo de error interno (0 en exito).
    stage : str
        Fase donde termino: `validation` (fallo resolver/validar el
        evento) o `controller` (el controller se ejecuto).
    status : int | None
        HTTP status explicito que el controller pide para esta respuesta
        (ej. 404, 409, 423, 429 en errores de negocio; 204 en exito sin
        body). `None` -> el http_handler usa su default (`success_status`
        en exito, 400 en error de negocio sin status). Permite que un
        controller exprese el status HTTP exacto sin tener que levantar
        una ApplicationError. Los handlers no-HTTP (SQS workers) lo
        ignoran.
    """

    is_valid: bool
    data: dict[str, Any]
    code: int
    stage: str
    status: int | None = None


def run_controller(
    synthetic_event: dict[str, Any],
    event_model: EventModelClass,
) -> DispatchResult:
    """Valida el evento, resuelve el controller y ejecuta su ciclo `run()`.

    Parameters
    ----------
    synthetic_event : dict[str, Any]
        Evento ya traducido al contrato `{operation, action, data}` por
        el `handler.py` del Lambda.
    event_model : EventModelClass
        Clase `EventModel` del Lambda (de `build_event_model(OPERATIONS)`).

    Returns
    -------
    DispatchResult
        `stage='validation'` si fallo resolver/validar el evento;
        `stage='controller'` si el controller se ejecuto (revisar
        `is_valid` para distinguir exito de error de negocio).
    """
    validation_result = validate_event(synthetic_event, event_model)
    if not validation_result.get('is_valid'):
        return DispatchResult(
            is_valid=False,
            data=validation_result.get('data', {}),
            code=validation_result.get('code', 6000),
            stage='validation',
        )

    validated_event = validation_result['data']
    controller_data = validated_event.controller_info.get('data', {})
    controller_class = controller_data.get('controller_class')

    instance = controller_class(event=validated_event.controller_event)
    result = instance.run()

    return DispatchResult(
        is_valid=bool(result.get('is_valid')),
        data=result.get('data', {}),
        code=result.get('code', 0),
        stage='controller',
        status=result.get('status'),
    )
