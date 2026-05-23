"""Helpers para los tests de http_handler.

Builders que arman un EventModel con un controller fake registrado, sin
depender del `controllers/` de un Lambda real. Prefijo `_` para que
pytest no recolecte este modulo como test.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import patch

from pydantic import BaseModel
from shared.lambda_kit import BaseController, build_event_model


class _FakeModel(BaseModel):
    """Modelo Pydantic minimo que acepta cualquier campo."""

    model_config = {'extra': 'allow'}


def make_fake_controller(
    execute_result: dict[str, Any] | None = None,
) -> type[BaseController]:
    """Construye una subclase de BaseController con un execute fijo."""
    result = execute_result or {'is_valid': True, 'data': {'ok': True}, 'code': 0}

    class _FakeCtrl(BaseController):
        event_model = _FakeModel

        def execute(self) -> dict:
            return result

    return _FakeCtrl


def with_registered_controller(
    operation: str,
    action: str,
    controller_cls: type[BaseController],
) -> tuple[type[BaseModel], Callable[..., Any]]:
    """Devuelve (EventModel, patcher) listos para usar.

    `patcher` es un context manager que monkey-patchea `import_controller`
    para devolver el `controller_cls` cuando se pida `(operation, action)`.
    """
    operations = {operation: {'controller': operation, 'arn_key': ''}}
    event_model = build_event_model(operations)

    def _fake_import_controller(
        op: str, act: str, _operations: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        if op != operation or act != action:
            return {
                'is_valid': False,
                'data': {'message': f'no controller for {op}/{act}'},
            }
        return {
            'is_valid': True,
            'data': {'controller_class': controller_cls},
        }

    patcher = patch(
        'shared.lambda_kit.event_model.import_controller',
        side_effect=_fake_import_controller,
    )
    return event_model, patcher
