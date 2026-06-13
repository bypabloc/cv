"""Error de negocio compartido por los services del Lambda `cv` (operations admin).

El controller lo captura y lo traduce a la respuesta normalizada
`{is_valid: False, data, code, status}`. Rangos del contrato
lambda-controller: `1xxx` validacion (UNKNOWN_NICHE,
REORDER_SLUGS_MISMATCH), `4xxx` negocio (SLUG_NOT_FOUND), `5xxx`
API externa (GITHUB_API_ERROR).
"""

from __future__ import annotations

from typing import Any


class ServiceError(Exception):
    """Error de negocio de un service del Lambda `cv` (operations admin)."""

    def __init__(
        self,
        message: str,
        *,
        code: int = 4000,
        error_code: str = 'SERVICE_ERROR',
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_code = error_code
        self.detail = detail or {}
