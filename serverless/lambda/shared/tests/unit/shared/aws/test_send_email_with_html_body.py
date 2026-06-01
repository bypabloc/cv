"""shared.aws.ses.send_email — request multipart con html_body.

Given un text_body y un html_body,
When invoco send_email,
Then el cliente sesv2 recibe Content.Simple.Body con AMBOS Text y Html
     (multipart).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from shared.aws.ses import send_email

pytestmark = pytest.mark.unit


def test_send_email_with_html_body() -> None:
    # Arrange
    fake_client = MagicMock()
    fake_client.send_email.return_value = {'MessageId': 'msg-456'}

    # Act
    with patch('shared.aws.ses._client', return_value=fake_client):
        send_email(
            from_address='no-reply@x.com',
            to_addresses=['a@x.com'],
            subject='Hi',
            text_body='plain',
            html_body='<p>plain</p>',
        )

    # Assert
    expected_body = {
        'Text': {'Data': 'plain', 'Charset': 'UTF-8'},
        'Html': {'Data': '<p>plain</p>', 'Charset': 'UTF-8'},
    }
    _kwargs = fake_client.send_email.call_args.kwargs
    assert _kwargs['Content']['Simple']['Body'] == expected_body
