"""
Given una identidad SES verificada en moto,
When shared.aws.ses.ses.send_email envia un email transaccional,
Then SES acepta el envio y devuelve un MessageId.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_ses_send_email_e2e(ses_identity: str) -> None:
    """send_email contra SES (moto) devuelve un MessageId."""
    # Arrange: leer el cliente del modulo via importlib para ver el
    # rebind del fixture (un `from ... import ses` capturaria el viejo;
    # `import shared.aws.ses as X` resuelve al re-export del package).
    import importlib

    ses = importlib.import_module('shared.aws.ses').ses

    # Act
    response = ses.send_email(
        FromEmailAddress=ses_identity,
        Destination={'ToAddresses': ['owner@example.com']},
        Content={
            'Simple': {
                'Subject': {'Data': 'Nuevo contacto'},
                'Body': {
                    'Text': {'Data': 'Hola desde el portfolio'},
                    'Html': {'Data': '<p>Hola desde el portfolio</p>'},
                },
            },
        },
    )

    # Assert
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200
    assert isinstance(response['MessageId'], str)
    assert len(response['MessageId']) > 0
