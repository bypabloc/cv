"""
Given un payload dict y una cola SQS fake (moto),
When send_to_queue se invoca,
Then el MessageBody en SQS coincide con json.dumps(payload).
"""

import json

import boto3
import pytest
from moto import mock_aws


@mock_aws
def test_send_to_queue_publishes_payload_to_sqs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange: setup moto SQS + SSM
    sqs = boto3.client('sqs', region_name='us-east-1')
    url = sqs.create_queue(QueueName='portfolio-test-queue')['QueueUrl']

    ssm = boto3.client('ssm', region_name='us-east-1')
    ssm.put_parameter(
        Name='/portfolio/test/sqs/test-queue/url',
        Value=url,
        Type='String',
    )

    monkeypatch.setenv(
        'SSM_TEST_QUEUE_QUEUE_URL_PATH',
        '/portfolio/test/sqs/test-queue/url',
    )

    # Clear ssm cache para que resuelva fresh
    import shared.aws.ssm as ssm_module
    if hasattr(ssm_module, 'get_secret') and hasattr(
        ssm_module.get_secret, 'cache_clear'
    ):
        ssm_module.get_secret.cache_clear()

    from shared.queue.publisher import send_to_queue

    payload = {
        'contact_id': '01900000-0000-7000-8000-000000000001',
        'name': 'Test',
        'message': 'Hola, con ñ y é',
    }

    # Act
    msg_id = send_to_queue(queue_short_name='test-queue', payload=payload)

    # Assert
    assert msg_id
    received = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=1)
    body = json.loads(received['Messages'][0]['Body'])
    assert body == payload


def test_resolve_queue_url_raises_when_env_var_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Given la env var SSM_<X>_QUEUE_URL_PATH no esta seteada,
    When send_to_queue se invoca,
    Then lanza RuntimeError con el nombre de la env var esperada.
    """
    monkeypatch.delenv('SSM_MISSING_QUEUE_URL_PATH', raising=False)
    from shared.queue.publisher import _resolve_queue_url

    with pytest.raises(RuntimeError) as exc:
        _resolve_queue_url('missing')

    assert 'SSM_MISSING_QUEUE_URL_PATH' in str(exc.value)
