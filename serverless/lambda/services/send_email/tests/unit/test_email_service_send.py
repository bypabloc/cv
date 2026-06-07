"""email_service.send: config DynamoDB + template S3 + render + SES.

Given email-config[kind] + templates en S3 (moto),
When se llama send,
Then renderiza con Jinja2 y llama SES con subject/html/text correctos.

Los helpers SSM (`get_parameter` para el nombre de tabla, `get_parameter_by_name`
para el from-address) se parchean: el provider de Powertools cachea un cliente
boto3 que moto no intercepta. DynamoDB + S3 SI van por moto (clientes lazy
creados dentro del mock).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit

_TABLE = 'portfolio-email-config-dev'
_BUCKET = 'portfolio-email-templates-dev'


def _seed():
    """Crea la tabla email-config + el bucket con un template, via moto."""
    import boto3

    ddb = boto3.client('dynamodb', region_name='us-east-1')
    ddb.create_table(
        TableName=_TABLE,
        AttributeDefinitions=[{'AttributeName': 'kind', 'AttributeType': 'S'}],
        KeySchema=[{'AttributeName': 'kind', 'KeyType': 'HASH'}],
        BillingMode='PAY_PER_REQUEST',
    )
    boto3.resource('dynamodb', region_name='us-east-1').Table(_TABLE).put_item(
        Item={
            'kind': 'login-code',
            'bucket': _BUCKET,
            'html_path': 'login-code.html',
            'txt_path': 'login-code.txt',
            'subject': 'Tu codigo: {{ code }}',
        }
    )
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket=_BUCKET)
    s3.put_object(
        Bucket=_BUCKET,
        Key='login-code.html',
        Body=b'<p>Codigo: {{ code }} ({{ expires_in_min }} min)</p>',
    )
    s3.put_object(Bucket=_BUCKET, Key='login-code.txt', Body=b'Codigo: {{ code }}')


def test_send_renders_and_calls_ses():
    from moto import mock_aws
    from shared.aws.dynamodb import reset_resource_cache
    from shared.aws.s3 import reset_client_cache

    with mock_aws():
        reset_resource_cache()
        reset_client_cache()
        _seed()

        from services import email_service

        with (
            patch(
                'services.email_service.get_parameter', return_value=_TABLE
            ),
            patch(
                'services.email_service.get_parameter_by_name',
                return_value='no-reply@the-full-stack.com',
            ),
            patch(
                'services.email_service.send_email',
                return_value={'MessageId': 'msg-1'},
            ) as mock_ses,
        ):
            message_id = email_service.send(
                kind='login-code',
                to=['user@example.com'],
                data={'code': 'XYZ789', 'expires_in_min': 15},
            )

    assert message_id == 'msg-1'
    call = mock_ses.call_args.kwargs
    assert call['to_addresses'] == ['user@example.com']
    assert call['subject'] == 'Tu codigo: XYZ789'
    assert call['html_body'] == '<p>Codigo: XYZ789 (15 min)</p>'
    assert call['text_body'] == 'Codigo: XYZ789'
    assert call['from_address'] == 'The Full Stack <no-reply@the-full-stack.com>'


def test_send_unknown_kind_raises_without_ses():
    from moto import mock_aws
    from services.email_service import EmailServiceError
    from shared.aws.dynamodb import reset_resource_cache

    with mock_aws():
        reset_resource_cache()
        _seed()  # solo tiene login-code

        from services import email_service

        with (
            patch('services.email_service.get_parameter', return_value=_TABLE),
            patch('services.email_service.send_email') as mock_ses,
            pytest.raises(EmailServiceError) as exc_info,
        ):
            email_service.send(
                kind='nonexistent-kind',
                to=['user@example.com'],
                data={},
            )

    assert exc_info.value.code == 1404
    assert exc_info.value.error_code == 'EMAIL_KIND_NOT_FOUND'
    mock_ses.assert_not_called()
