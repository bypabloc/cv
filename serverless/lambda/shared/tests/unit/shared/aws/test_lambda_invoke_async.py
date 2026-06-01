"""shared.aws.lambda_invoke.invoke_async invoca con InvocationType=Event.

Given un function_name + payload,
When se llama invoke_async,
Then el cliente Lambda recibe InvocationType='Event' y el Payload JSON exacto.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
import shared.aws.lambda_invoke as lambda_invoke
from shared.aws.lambda_invoke import LambdaInvokeError

pytestmark = pytest.mark.unit


def test_invoke_async_uses_event_invocation_type(monkeypatch):
    # Arrange: cliente Lambda mockeado
    mock_client = MagicMock()
    monkeypatch.setattr(lambda_invoke, '_client', lambda: mock_client)

    # Act
    lambda_invoke.invoke_async(
        function_name='portfolio-send-email-dev',
        payload={'operation': 'email', 'action': 'send', 'data': {'kind': 'x'}},
    )

    # Assert
    call = mock_client.invoke.call_args
    assert call.kwargs['FunctionName'] == 'portfolio-send-email-dev'
    assert call.kwargs['InvocationType'] == 'Event'
    assert json.loads(call.kwargs['Payload']) == {
        'operation': 'email',
        'action': 'send',
        'data': {'kind': 'x'},
    }


def test_invoke_async_raises_lambda_invoke_error_on_failure(monkeypatch):
    # Arrange: el cliente lanza al invocar
    mock_client = MagicMock()
    mock_client.invoke.side_effect = RuntimeError('access denied')
    monkeypatch.setattr(lambda_invoke, '_client', lambda: mock_client)

    # Act + Assert
    with pytest.raises(LambdaInvokeError):
        lambda_invoke.invoke_async(
            function_name='portfolio-send-email-dev',
            payload={'k': 'v'},
        )
