"""Handler — fallo de SQS devuelve error explicito (no fallback a sync).

Given ASYNC_MODE=true + SQS down (`send_to_queue` lanza QueuePublishError),
When lambda_handler procesa el request,
Then NO hace fallback a Neon sync (eso seria un bug oculto). El error
     propaga al `http_handler`, que lo traduce a HTTP 502 con un body
     JSON que reporta el problema upstream.

AC-8 del plan lambdas-async-sqs (errores transparentes, no degradacion
silenciosa).
"""

import json

import pytest

from tests.unit._helpers import api_gw_event, lambda_context, valid_body

pytestmark = pytest.mark.unit


def test_enqueue_failure_returns_error(
    async_mode: None,
    monkeypatch: pytest.MonkeyPatch,
    tracking_aws: None,
) -> None:
    import handler
    from shared.queue import QueuePublishError

    # Arrange: el publish lanza un error simulando SQS caido.
    def _explode(**kwargs: object) -> str:
        raise QueuePublishError(
            'tracking-events', RuntimeError('SQS unavailable')
        )

    monkeypatch.setattr('services.tracking_service.send_to_queue', _explode)

    event = api_gw_event(body=valid_body())

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert: 5xx upstream, no degradacion silenciosa a 202.
    # error_response() para excepciones genericas usa status 500 y un body
    # con shape estable: {error, code}. NO se filtra el detalle del SQS
    # al cliente (eso esta en CloudWatch logs).
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body == {'error': 'Internal server error', 'code': 'INTERNAL_ERROR'}
