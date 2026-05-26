"""Test: ContactQueueMessage valida la forma del body SQS.

Given un mensaje SQS con `contact_id` que NO es UUID v7 valido,
When ContactQueueMessage lo valida con Pydantic,
Then levanta ValidationError (el handler lo capturara y marcara el
     record como batchItemFailure para retry SQS).

Spec lambdas-async-sqs (fase 05): el modelo usa `extra='forbid'` para
rechazar campos no declarados (defensa ante un encoder que publique con
un schema distinto sin bumpear `schema_version`).
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_message_model_rejects_short_contact_id():
    """contact_id menor a 36 caracteres -> ValidationError."""
    from models.message import ContactQueueMessage

    base_payload = {
        'schema_version': 1,
        'contact_id': 'short-id',  # < 36 chars
        'created_at': datetime(2026, 5, 25, 18, 0, 0).isoformat(),
        'session_id': 'cf-019e5c50-0000-7000-8000-000000000099',
        'name': 'Pablo',
        'email': 'p@example.com',
        'message': 'Hola mundo de prueba para el worker',
        'ip': '203.0.113.10',
    }

    with pytest.raises(ValidationError) as exc_info:
        ContactQueueMessage.model_validate(base_payload)

    # Assert: el error es sobre contact_id (string demasiado corto).
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'] == ('contact_id',)
    assert errors[0]['type'] == 'string_too_short'
