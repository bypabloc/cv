"""shared.observability re-exporta MetricUnit.

Given el subpaquete shared.observability,
When importo MetricUnit desde shared.observability,
Then es exactamente la misma clase que aws_lambda_powertools.metrics
     exporta y los services pueden usarla sin importar Powertools directo.
"""

from __future__ import annotations

import pytest
from aws_lambda_powertools.metrics import MetricUnit as PowertoolsMetricUnit
from shared.observability import MetricUnit

pytestmark = pytest.mark.unit


def test_metric_unit_is_powertools_class() -> None:
    # Arrange + Act + Assert
    assert MetricUnit is PowertoolsMetricUnit


def test_metric_unit_count_value() -> None:
    # Arrange + Act + Assert
    assert MetricUnit.Count.value == 'Count'


def test_metric_unit_milliseconds_value() -> None:
    # Arrange + Act + Assert
    assert MetricUnit.Milliseconds.value == 'Milliseconds'
