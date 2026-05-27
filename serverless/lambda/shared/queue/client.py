"""@module client — cliente SQS cacheado para invocaciones warm.

El cliente boto3 SQS se crea UNA vez a module-scope (mismo patron que
shared.aws.ssm). Reutilizado entre invocaciones warm del mismo Lambda.
"""

import os
from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config


@lru_cache(maxsize=1)
def get_sqs_client() -> Any:
    """Cliente boto3.client('sqs') cacheado.

    Region default: us-east-1 (override con AWS_REGION env var).
    Retries y timeouts conservadores para no bloquear el encoder.
    """
    region = os.environ.get('AWS_REGION', 'us-east-1')
    return boto3.client(
        'sqs',
        region_name=region,
        config=Config(
            retries={'max_attempts': 3, 'mode': 'standard'},
            connect_timeout=2,
            read_timeout=5,
        ),
    )
