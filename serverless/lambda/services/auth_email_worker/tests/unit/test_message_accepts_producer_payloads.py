"""Test: AuthEmailMessage acepta los payloads que emiten los productores.

Guard de regresion del contrato productor->consumidor. Los productores
(`auth` EmailDispatchService, `users` EmailDispatchService) arman un dict
con shape `{kind, to, user_id, niche, subject_id, data}` y lo encolan. El
worker lo valida con AuthEmailMessage (`extra='forbid'`). Si un productor
agrega un campo extra (`schema_version`, `locale`) o omite `subject_id`,
el worker RECHAZA el mensaje y nunca se envia el email (termina en la DLQ).

Este test reconstruye los payloads canonicos de cada productor y verifica
que el modelo del worker los acepta; ademas verifica que el shape buggy
viejo (con schema_version/locale y SIN subject_id) es rechazado.
"""

import pytest

pytestmark = pytest.mark.unit

_UID = '01900000-0000-7000-8000-000000000001'

# Payloads canonicos tal cual los emite cada productor (mantener alineado
# con services/auth/.../email_dispatch_service.py y
# services/users/.../email_dispatch_service.py).
_PRODUCER_PAYLOADS = [
    {
        'kind': 'register-magic-link',
        'to': 'u@x.com',
        'user_id': _UID,
        'niche': 'fintech',
        'subject_id': 'auth.register-magic-link.subject',
        'data': {'verify_url': 'https://api.x/auth?token=T', 'expires_in_min': 15},
    },
    {
        'kind': 'register-code',
        'to': 'u@x.com',
        'user_id': _UID,
        'niche': None,
        'subject_id': 'auth.register-code.subject',
        'data': {'code': 'ABCDEFGH', 'expires_in_min': 15},
    },
    {
        'kind': 'login-magic-link',
        'to': 'u@x.com',
        'user_id': _UID,
        'niche': None,
        'subject_id': 'auth.login-magic-link.subject',
        'data': {'verify_url': 'https://api.x/auth?token=T', 'expires_in_min': 15},
    },
    {
        'kind': 'email-change-verify',
        'to': 'new@x.com',
        'user_id': _UID,
        'niche': None,
        'subject_id': 'auth.users.email-change-verify.subject',
        'data': {
            'new_email': 'new@x.com',
            'verify_url': 'https://api.x/users?token=T',
            'expires_in_min': 15,
        },
    },
    {
        'kind': 'account-deleted',
        'to': 'u@x.com',
        'user_id': _UID,
        'niche': None,
        'subject_id': 'auth.users.account-deleted.subject',
        'data': {},
    },
]


@pytest.mark.parametrize('payload', _PRODUCER_PAYLOADS)
def test_message_accepts_producer_payload(payload):
    """AuthEmailMessage valida cada payload canonico de los productores."""
    from models.message import AuthEmailMessage

    msg = AuthEmailMessage(**payload)

    assert msg.kind == payload['kind']
    assert str(msg.user_id) == _UID
    assert msg.subject_id == payload['subject_id']


def test_message_rejects_old_buggy_shape():
    """El shape viejo (schema_version/locale, SIN subject_id) es rechazado.

    Documenta el bug pre-existente: el productor `auth` publicaba este
    shape y el worker lo rechazaba -> los emails de register/login nunca
    se enviaban.
    """
    from models.message import AuthEmailMessage
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AuthEmailMessage(
            schema_version=1,
            kind='register-magic-link',
            to='u@x.com',
            user_id=_UID,
            niche='fintech',
            locale='es',
            data={'token': 'T', 'verify_url': 'https://api.x/auth?token=T'},
        )
