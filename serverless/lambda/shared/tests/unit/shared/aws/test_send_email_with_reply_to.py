"""shared.aws.ses.send_email — request con ReplyToAddresses.

Given un reply_to no vacio,
When invoco send_email,
Then el payload incluye ReplyToAddresses con esa lista.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from shared.aws import send_email

pytestmark = pytest.mark.unit


def test_send_email_with_reply_to() -> None:
    # Arrange
    fake_client = MagicMock()
    fake_client.send_email.return_value = {'MessageId': 'msg-789'}

    # Act
    with patch('shared.aws.ses._client', return_value=fake_client):
        send_email(
            from_address='no-reply@x.com',
            to_addresses=['a@x.com'],
            subject='Hi',
            text_body='plain',
            reply_to=['contact@user.com'],
        )

    # Assert
    _kwargs = fake_client.send_email.call_args.kwargs
    assert _kwargs['ReplyToAddresses'] == ['contact@user.com']


def test_send_email_without_reply_to_omits_field() -> None:
    # Arrange
    fake_client = MagicMock()
    fake_client.send_email.return_value = {'MessageId': 'msg-aaa'}

    # Act
    with patch('shared.aws.ses._client', return_value=fake_client):
        send_email(
            from_address='no-reply@x.com',
            to_addresses=['a@x.com'],
            subject='Hi',
            text_body='plain',
        )

    # Assert: la key ReplyToAddresses no debe aparecer en el payload
    _kwargs = fake_client.send_email.call_args.kwargs
    assert 'ReplyToAddresses' not in _kwargs
