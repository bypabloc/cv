"""SnapStart warmup hook generico para lambdas Python con snap_start=true.

Pre-calienta handshakes TLS de los clientes boto3 indicados ANTES de que
SnapStart tome el snapshot (durante PublishVersion). El snapshot Firecracker
captura el cliente boto3 con su conexion HTTPS abierta + cert chain
verificado. Post-restore, la primera invocacion reutiliza esa conexion:
handshake ya hecho, gana 200-500ms por servicio AWS.

Uso (module-scope del handler, NO dentro del handler):

    from shared.lambda_kit.snap_start_warmup import register_warmup
    register_warmup(clients=['sqs', 'dynamodb', 'ssm'])

Soporta: sqs, dynamodb, ssm, ses, kms. Cada warmup call corre con
try/except: si falla (AWS 5xx transitorio, permisos IAM faltantes), loguea
WARNING y continua. NUNCA aborta el INIT.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from typing import Any

import boto3
from botocore.config import Config

# Logger basico (NO usa shared.observability.logger porque tiene
# dependencias de Powertools que pueden no estar listas en module-scope
# muy temprano del INIT). logging stdlib es siempre safe.
_logger = logging.getLogger('snap_start_warmup')


# Calls de warmup soportados. Cada uno hace handshake TLS + sigv4 sin
# tocar recursos del proyecto.
_WARMUP_CALLS: dict[str, Callable[[Any], Any]] = {
    'sqs': lambda c: c.list_queues(MaxResults=1),
    'dynamodb': lambda c: c.describe_endpoints(),
    'ssm': lambda c: c.describe_parameters(MaxResults=1),
    'ses': lambda c: c.list_email_identities(PageSize=1),
    'kms': lambda c: c.list_keys(Limit=1),
}


def _build_client(service: str, region: str) -> Any:
    """boto3.client con timeouts conservadores (NO debe colgar el INIT)."""
    boto_service = 'sesv2' if service == 'ses' else service
    return boto3.client(
        boto_service,
        region_name=region,
        config=Config(
            retries={'max_attempts': 1, 'mode': 'standard'},
            connect_timeout=3,
            read_timeout=3,
        ),
    )


def register_warmup(clients: list[str]) -> None:
    """Pre-calienta handshakes TLS de los clientes boto3 indicados.

    Args:
        clients: lista de servicios soportados (sqs, dynamodb, ssm, ses, kms).

    Raises:
        ValueError: si algun client no esta soportado (defensa fail-fast
            contra typo en el manifest del lambda). Se levanta ANTES de
            hacer cualquier call AWS.

    Notes:
        - Llama SOLO desde module-scope del handler del lambda.
        - Cada warmup call tiene try/except: si falla, loguea WARNING y
          continua con los demas.
        - Si la lista esta vacia, no-op silencioso.
    """
    if not clients:
        return

    # Defensa fail-fast: typo en manifest aborta INIT con error claro.
    unsupported = [c for c in clients if c not in _WARMUP_CALLS]
    if unsupported:
        raise ValueError(
            f'snap_start_warmup: clientes no soportados: {unsupported}. '
            f'Soportados: {sorted(_WARMUP_CALLS)}'
        )

    region = os.environ.get('AWS_REGION', 'us-east-1')

    for client_name in clients:
        warmup_call = _WARMUP_CALLS[client_name]
        try:
            start = time.perf_counter()
            client = _build_client(client_name, region)
            warmup_call(client)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            _logger.info(
                '[snap_start_warmup] %s: ok (%dms)',
                client_name,
                elapsed_ms,
            )
        except Exception as exc:
            _logger.warning(
                '[snap_start_warmup] %s: failed (%s: %s)',
                client_name,
                type(exc).__name__,
                exc,
            )
