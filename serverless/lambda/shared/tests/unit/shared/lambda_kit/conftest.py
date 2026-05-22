"""Fixtures para los tests de shared.lambda_kit.

`make_controller` construye subclases sinteticas de `BaseController`
sin depender del `controllers/` de ningun Lambda real.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from pydantic import BaseModel
from shared.lambda_kit.base_controller import BaseController

ControllerFactory = Callable[..., type[BaseController]]


@pytest.fixture
def make_controller() -> ControllerFactory:
    """Devuelve un builder de subclases de `BaseController` para tests.

    El builder acepta `execute_result`, `event_model` y `arn_config_key`
    y devuelve una clase controller lista para instanciar.
    """

    def _build(
        *,
        execute_result: dict[str, Any] | None = None,
        event_model: type[BaseModel] | None = None,
        arn_config_key: str = '',
    ) -> type[BaseController]:
        result = execute_result or {
            'is_valid': True,
            'data': {},
            'code': 0,
        }

        class _Controller(BaseController):
            def execute(self) -> dict:
                return result

        _Controller.event_model = event_model
        _Controller.arn_config_key = arn_config_key
        return _Controller

    return _build
