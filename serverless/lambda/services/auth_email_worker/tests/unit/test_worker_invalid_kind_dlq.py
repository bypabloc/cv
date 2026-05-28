"""Test: AuthEmailMessage rechaza kinds desconocidos.

Given un mensaje SQS con `kind` que NO esta en SUPPORTED_KINDS,
When AuthEmailMessage lo valida con Pydantic,
Then levanta ValidationError (el handler lo capturara y marcara el
     record como batchItemFailure → SQS reintenta → DLQ tras
     max_receive_count=3).

Plan 01-auth-infra-basics: kinds invalidos = mensaje malformado = DLQ.
"""

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_message_model_rejects_unknown_kind():
    """kind no soportado -> ValidationError sobre el discriminador."""
    from models.message import AuthEmailMessage

    base_payload = {
        'kind': 'unknown-kind',
        'to': 'user@example.com',
        'user_id': '019e5c50-0000-7000-8000-000000000001',
        'niche': None,
        'subject_id': 'auth.unknown.subject',
        'data': {},
    }

    with pytest.raises(ValidationError) as exc_info:
        AuthEmailMessage.model_validate(base_payload)

    # Assert: el error es sobre kind (Literal mismatch).
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'] == ('kind',)
    assert errors[0]['type'] == 'literal_error'
