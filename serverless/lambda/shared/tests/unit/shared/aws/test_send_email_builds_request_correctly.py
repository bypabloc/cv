"""shared.aws.ses.send_email — request basico con solo text_body.

Given un text_body y sin html_body ni reply_to,
When invoco send_email,
Then el cliente sesv2 recibe el payload con Content.Simple.Subject,
     Body.Text (sin Body.Html), Destination.ToAddresses y SIN
     ReplyToAddresses.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from shared.aws import send_email

pytestmark = pytest.mark.unit


def test_send_email_builds_request_correctly() -> None:
    # Arrange
    fake_client = MagicMock()
    fake_client.send_email.return_value = {'MessageId': 'msg-123'}

    # Act
    with patch('shared.aws.ses._client', return_value=fake_client):
        response = send_email(
            from_address='no-reply@the-full-stack.com',
            to_addresses=['owner@example.com'],
            subject='Hello',
            text_body='Plain hello',
        )

    # Assert
    assert response == {'MessageId': 'msg-123'}
    fake_client.send_email.assert_called_once_with(
        FromEmailAddress='no-reply@the-full-stack.com',
        Destination={'ToAddresses': ['owner@example.com']},
        Content={
            'Simple': {
                'Subject': {'Data': 'Hello', 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': 'Plain hello', 'Charset': 'UTF-8'},
                },
            },
        },
    )
