"""Error de negocio compartido por los services del Lambda `analytics`.

El controller lo captura y lo traduce a la respuesta normalizada
`{is_valid: False, data, code}`. Para errores transitorios de DB se usa
`code=5100` (503); para "no encontrado" `code=4040` (404).
"""

from __future__ import annotations


class ServiceError(Exception):
    """Error de negocio de un service del Lambda `analytics`."""

    def __init__(
        self,
        message: str,
        *,
        code: int = 5100,
        error_code: str = 'SERVICE_ERROR',
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_code = error_code


class NotFoundError(ServiceError):
    """Recurso no encontrado (ej. sessions/detail con session_id inexistente)."""

    def __init__(self, message: str = 'not found') -> None:
        super().__init__(message, code=4040, error_code='NOT_FOUND')
