"""shared.lambda_kit.log_metrics.LogMetricType.

Given el enum LogMetricType base del kit,
When se inspeccionan sus miembros,
Then los tipos del ciclo de vida del lambda-controller estan presentes
     con su valor string.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.log_metrics import LogMetricType

pytestmark = pytest.mark.unit


def test_log_metrics_base_members() -> None:
    # Assert
    assert LogMetricType.PHASE_START.value == 'PHASE_START'
    assert LogMetricType.PHASE_COMPLETE.value == 'PHASE_COMPLETE'
    assert LogMetricType.PRELOAD_PHASE_FAILED.value == 'PRELOAD_PHASE_FAILED'
    assert (
        LogMetricType.VALIDATE_PHASE_FAILED.value
        == 'VALIDATE_PHASE_FAILED'
    )
    assert (
        LogMetricType.EXECUTE_PHASE_FAILED.value == 'EXECUTE_PHASE_FAILED'
    )
    assert LogMetricType.INVALID_OPERATION.value == 'INVALID_OPERATION'
