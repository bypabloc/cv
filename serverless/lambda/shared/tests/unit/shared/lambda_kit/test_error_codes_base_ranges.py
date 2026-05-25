"""shared.lambda_kit.error_codes.ErrorCode.

Given el enum ErrorCode base del kit,
When se inspeccionan sus miembros,
Then los codigos base estan en los rangos esperados (0/1xxx/2xxx/4xxx/
     5xxx/6xxx).
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.error_codes import ErrorCode

pytestmark = pytest.mark.unit


def test_error_codes_base_ranges() -> None:
    # Assert
    assert ErrorCode.SUCCESS.value == 0
    assert ErrorCode.VALIDATION_ERROR.value == 1000
    assert ErrorCode.CONFIGURATION_MISSING.value == 2001
    assert ErrorCode.BUSINESS_LOGIC_ERROR.value == 4000
    assert ErrorCode.EXTERNAL_API_ERROR.value == 5000
    assert ErrorCode.UNEXPECTED_ERROR.value == 6000
