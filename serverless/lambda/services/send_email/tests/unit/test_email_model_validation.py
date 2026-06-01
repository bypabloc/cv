"""EmailSendRequest valida el payload del envio de email.

Given un payload con/sin campos requeridos,
When se valida con EmailSendRequest,
Then acepta el valido y rechaza kind/to faltantes.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_email_model_accepts_valid_payload():
    from models.email import EmailSendRequest

    model = EmailSendRequest(
        kind='register-code',
        to=['user@example.com'],
        data={'code': 'ABC123', 'expires_in_min': 15},
    )
    assert model.kind == 'register-code'
    assert model.to == ['user@example.com']
    assert model.data == {'code': 'ABC123', 'expires_in_min': 15}
    assert model.reply_to is None


def test_email_model_rejects_missing_kind():
    from models.email import EmailSendRequest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        EmailSendRequest(to=['user@example.com'])


def test_email_model_rejects_empty_to():
    from models.email import EmailSendRequest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        EmailSendRequest(kind='login-code', to=[])
