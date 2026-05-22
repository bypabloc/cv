"""Runner del Lambda `stream_processor` para los tests de integracion.

Prefijo `_` en la carpeta para que pytest NO recolecte estos archivos
como tests. Encapsula el unico patron de invoke de la suite: parchear
`stream_service.db_session` con el context manager SQLite y llamar al
`lambda_handler` real.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

from sqlalchemy import Engine

from tests.integration._fixtures.db import make_db_session
from tests.integration._fixtures.events import lambda_context


def invoke_handler(
    event: dict[str, Any],
    engine: Engine,
) -> dict[str, Any]:
    """Invoca el `lambda_handler` real con la base SQLite del test.

    Parametros
    ----------
    event : dict[str, Any]
        Evento DynamoDB Stream crudo (`{Records: [...]}`).
    engine : Engine
        Engine SQLite in-memory de la fixture `sqlite_db`.

    Returns
    -------
    dict[str, Any]
        La respuesta del handler: `{batchItemFailures: [...]}`.
    """
    from services import stream_service

    db_session = make_db_session(engine)
    with patch.object(stream_service, 'db_session', db_session):
        import handler

        return handler.lambda_handler(event, lambda_context())


@contextmanager
def patched_validation(
    error_message: str = 'Operacion no es valida',
) -> Iterator[None]:
    """Fuerza el fallo de la validacion del evento en el handler.

    El handler sintetiza SIEMPRE un evento valido
    (`operation='stream', action='process'`); para ejercitar la rama de
    validacion fallida se parchea `validate_event` para que devuelva una
    respuesta de error normalizada. El handler real (logger incluido)
    corre sin mocks adicionales.
    """
    import handler

    error_response = {
        'is_valid': False,
        'code': 1001,
        'status': 1001,
        'message': error_message,
        'data': {},
    }
    with patch.object(handler, 'validate_event', return_value=error_response):
        yield
