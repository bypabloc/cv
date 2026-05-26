"""@module publisher — helper para encolar mensajes a SQS desde un encoder.

Resuelve la URL de la cola desde SSM (env var SSM_<NAME>_QUEUE_URL_PATH
inyectada por devtools). El path SSM se resuelve via shared.aws.ssm
(cached en cold start). El SQS client se cachea module-scope.
"""

from __future__ import annotations

import json
import os
from typing import Any

from aws_lambda_powertools.metrics import MetricUnit

from shared.aws.ssm import get_secret
from shared.observability.logger import logger
from shared.observability.metrics import metrics

from .client import get_sqs_client


class QueuePublishError(Exception):
    """Falla al publicar a SQS. El encoder lo propaga como 5xx."""

    def __init__(self, queue_short_name: str, cause: Exception) -> None:
        super().__init__(f'No se pudo publicar a {queue_short_name}: {cause}')
        self.queue_short_name = queue_short_name
        self.cause = cause


def _resolve_queue_url(short_name: str) -> str:
    """Resuelve la URL SQS desde SSM_<UPPER>_QUEUE_URL_PATH env var.

    short_name: nombre corto del catalogo ('contact-form', 'tracking-events').
    Convencion:
      'contact-form'    -> SSM_CONTACT_FORM_QUEUE_URL_PATH
      'tracking-events' -> SSM_TRACKING_EVENTS_QUEUE_URL_PATH
    """
    env_var = f'SSM_{short_name.upper().replace("-", "_")}_QUEUE_URL_PATH'
    ssm_path = os.environ.get(env_var)
    if not ssm_path:
        raise RuntimeError(
            f'{env_var} no esta seteada. devtools debe inyectarla cuando '
            f'el manifest declara uses.queues con la cola correspondiente.'
        )
    return get_secret(ssm_path)


def send_to_queue(
    *,
    queue_short_name: str,
    payload: dict[str, Any],
    message_attributes: dict[str, Any] | None = None,
) -> str:
    """Encola un mensaje JSON a SQS y retorna el MessageId."""
    sqs = get_sqs_client()
    queue_url = _resolve_queue_url(queue_short_name)

    body = json.dumps(payload, ensure_ascii=False, default=str)
    try:
        resp = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=body,
            MessageAttributes=message_attributes or {},
        )
    except Exception as exc:
        metrics.add_metric(
            name='QueuePublishFailed', unit=MetricUnit.Count, value=1,
        )
        logger.exception(
            'failed to publish message to SQS',
            extra={
                'queue': queue_short_name,
                'payload_keys': sorted(payload.keys()),
            },
        )
        raise QueuePublishError(queue_short_name, exc) from exc

    message_id: str = resp['MessageId']
    metrics.add_metric(name='QueuePublishOk', unit=MetricUnit.Count, value=1)
    logger.info(
        'message published to SQS',
        extra={
            'queue': queue_short_name,
            'message_id': message_id,
            'payload_keys': sorted(payload.keys()),
        },
    )
    return message_id
