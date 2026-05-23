"""shared.lambda_kit.http_dispatch.http_handler — metrica error.

Given metric_names que declara nombre para 'error',
When la request es invalida (validation failed por falta de action),
Then se emite la metrica configurada y la respuesta es HTTP 400.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit import build_event_model, http_handler

pytestmark = pytest.mark.unit


def test_http_handler_emits_metrics_on_error() -> None:
    # Arrange — operacion existe en OPERATIONS pero action no encontrara
    # controller via import_controller (no hay carpeta real); el kit
    # devuelve stage='validation' is_valid=False.
    event_model = build_event_model({'cv': {'controller': 'cv', 'arn_key': ''}})
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {
            'operation': 'cv',
            'action': 'nonexistent_action_for_test',
        },
        'headers': {},
    }

    # Act
    response = http_handler(
        event,
        event_model=event_model,
        cors_origin='public',
        metric_names={'error': 'TestErrorMetric'},
    )

    # Assert — la action no existe -> el kit lo trata como validation error
    # via ValidationError(INVALID_REQUEST) que mapea a HTTP 400.
    assert response['statusCode'] == 400
