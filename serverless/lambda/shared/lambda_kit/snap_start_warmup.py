"""SnapStart warmup hook generico para lambdas Python con snap_start=true.

Pre-instancia clientes boto3 ANTES de que SnapStart tome el snapshot
(durante PublishVersion). El snapshot Firecracker captura el cliente
boto3 con su endpoint resolver, sigv4 setup y configuracion HTTP pool
ya cargados. Post-restore, la primera invocacion paga SOLO el handshake
TLS (no el setup completo del cliente).

Por que NO hace calls AWS: los roles IAM del lambda suelen estar
scoped a recursos especificos (table arn, queue arn, parameter arn).
Hacer `sqs.list_queues()` o `ssm.describe_parameters()` requiere
permisos account-wide que NO tienen los roles least-privilege. El
warmup se limita a instanciar el cliente — el ahorro real viene de
evitar reparsear el endpoint, crear el connection pool y configurar
sigv4 en cada cold start.

Uso (module-scope del handler, NO dentro del handler):

    from shared.lambda_kit.snap_start_warmup import register_warmup
    register_warmup(clients=['sqs', 'dynamodb', 'ssm'])

Soporta: sqs, dynamodb, ssm, ses, kms, s3, lambda (cualquier servicio
boto3). Cada instanciacion corre con try/except: si falla (region
invalida, service typo), loguea WARNING y continua. NUNCA aborta el
INIT.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import boto3
from botocore.config import Config

# Logger basico (NO usa shared.observability.logger porque tiene
# dependencias de Powertools que pueden no estar listas en module-scope
# muy temprano del INIT). logging stdlib es siempre safe.
_logger = logging.getLogger('snap_start_warmup')


# Mapping de service short_name -> boto3 service name. La mayoria son
# identicos; 'ses' es 'sesv2' (preferimos v2).
_SERVICE_NAME_MAP: dict[str, str] = {
    'ses': 'sesv2',
}

# Whitelist de servicios soportados. Lista cerrada para defensa
# fail-fast contra typos en el manifest. Si necesitas otro, agregarlo
# aca + actualizar tests.
_SUPPORTED_CLIENTS: frozenset[str] = frozenset(
    {'sqs', 'dynamodb', 'ssm', 'ses', 'kms', 's3', 'lambda'}
)


def _build_client(service: str, region: str) -> Any:
    """boto3.client con timeouts conservadores (NO debe colgar el INIT)."""
    boto_service = _SERVICE_NAME_MAP.get(service, service)
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
    """Pre-instancia clientes boto3 antes del snapshot SnapStart.

    Args:
        clients: lista de servicios soportados (sqs, dynamodb, ssm, ses,
            kms, s3, lambda).

    Raises:
        ValueError: si algun client no esta soportado (defensa fail-fast
            contra typo en el manifest del lambda). Se levanta ANTES de
            instanciar cualquier cliente.

    Notes:
        - Llama SOLO desde module-scope del handler del lambda.
        - Cada instanciacion tiene try/except: si falla, loguea WARNING
          y continua con los demas.
        - Si la lista esta vacia, no-op silencioso.
        - Solo INSTANCIA el cliente — NO llama AWS. El ahorro viene de
          tener el endpoint resolver + sigv4 setup + connection pool ya
          cargados en el snapshot. La primera llamada post-restore paga
          el TLS handshake (~100-200ms) pero NO el setup completo
          (~200-400ms del cold start tradicional).
    """
    if not clients:
        return

    # Defensa fail-fast: typo en manifest aborta INIT con error claro.
    unsupported = [c for c in clients if c not in _SUPPORTED_CLIENTS]
    if unsupported:
        raise ValueError(
            f'snap_start_warmup: clientes no soportados: {unsupported}. '
            f'Soportados: {sorted(_SUPPORTED_CLIENTS)}'
        )

    region = os.environ.get('AWS_REGION', 'us-east-1')

    for client_name in clients:
        try:
            start = time.perf_counter()
            _build_client(client_name, region)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            _logger.info(
                '[snap_start_warmup] %s: ok (%dms)',
                client_name,
                elapsed_ms,
            )
        except Exception as exc:  # noqa: BLE001 — fail-safe deliberado
            _logger.warning(
                '[snap_start_warmup] %s: failed (%s: %s)',
                client_name,
                type(exc).__name__,
                exc,
            )
