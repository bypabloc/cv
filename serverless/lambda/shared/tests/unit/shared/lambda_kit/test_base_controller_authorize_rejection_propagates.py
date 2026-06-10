"""shared.lambda_kit.base_controller.BaseController.run (fase Authorize).

Given un controller con required_permission='admin' y un checker que
     RAISEA ApplicationError(404) (no-admin, anti-enumeration),
When se ejecuta run,
Then la ApplicationError propaga cruda (la captura http_handler) y
     preload/validate/execute NUNCA corren.
"""

from __future__ import annotations

import pytest
from shared.core.exceptions import ApplicationError
from shared.lambda_kit.base_controller import (
    BaseController,
    set_permission_checker,
)

pytestmark = pytest.mark.unit


def test_base_controller_authorize_rejection_propagates() -> None:
    # Arrange
    phases: list[str] = []

    def _checker(permission: str, meta: dict, *, action: str) -> object:
        raise ApplicationError(
            'NOT_FOUND',
            code='NOT_FOUND',
            status_code=404,
        )

    set_permission_checker(_checker)

    class _Controller(BaseController):
        required_permission = 'admin'

        def preload(self) -> dict:
            phases.append('preload')
            return super().preload()

        def validate(self) -> dict:
            phases.append('validate')
            return super().validate()

        def execute(self) -> dict:
            phases.append('execute')
            return {'is_valid': True, 'data': {}, 'code': 0}

    controller = _Controller(event={'_meta': {'authorization': None}})

    # Act / Assert
    with pytest.raises(ApplicationError) as exc_info:
        controller.run()

    assert exc_info.value.status_code == 404
    assert phases == []
