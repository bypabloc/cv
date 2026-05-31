"""@module shared.aws.warmup — precalentamiento de clientes boto3 en INIT.

`warm_aws_clients()` fuerza la creacion de los clientes boto3 (DynamoDB
resource, SQS client) en el module-scope del handler (fase INIT). En
Lambda, el INIT tiene CPU SIN throttle (y queda en el SNAPSHOT de
SnapStart), mientras que el EXECUTE a baja memoria recibe CPU
proporcional (~0.07 vCPU a 128 MB). boto3 construye el service model +
resuelve credenciales/endpoint en la PRIMERA creacion de cada cliente:
ese trabajo CPU caro, si cae en EXECUTE a 128 MB, tarda segundos y puede
agotar el timeout. Warmeandolo en INIT, el EXECUTE solo reusa el
singleton ya construido.

Es BEST-EFFORT: cualquier fallo (sin red, sin credenciales en un test) se
omite silenciosamente — NUNCA rompe el INIT. Mismo contrato que
`shared.db.warmup.warm_db`. Ver `.claude/rules/lambda-config.md`.
"""

from __future__ import annotations

from shared.observability.logger import logger


def warm_aws_clients(
    *,
    dynamodb: bool = False,
    sqs: bool = False,
    lambda_: bool = False,
) -> None:
    """Crea los clientes boto3 pedidos en INIT (best-effort, idempotente).

    Parameters
    ----------
    dynamodb : bool
        Warmea el resource boto3 DynamoDB (`shared.aws.dynamodb.get_resource`).
        Lo usan rate-limit (rules + buckets) y el cache.
    sqs : bool
        Warmea el cliente boto3 SQS (`shared.queue.client.get_sqs_client`).
        Lo usa el publisher (`send_to_queue`).
    lambda_ : bool
        Warmea el cliente boto3 Lambda (`shared.aws.lambda_invoke`). Lo usa
        `invoke_async` (invoke Lambda->Lambda, reemplazo de SQS).

    Cada cliente se cachea a module-scope en su modulo, asi que esta
    llamada solo paga la construccion una vez (las siguientes son no-op).
    """
    if dynamodb:
        try:
            from shared.aws.dynamodb import get_resource

            # `.meta.client` materializa el cliente low-level boto3 (el que
            # usa el ORM shared.dynamodb.BaseModel para get_item/query/
            # update_item). Construye el service model + resuelve
            # credenciales/endpoint en INIT (CPU sin throttle + snapshot),
            # no en el EXECUTE a 0.07 vCPU.
            _ = get_resource().meta.client
        except Exception as exc:
            logger.debug('warm dynamodb omitido: %s', type(exc).__name__)
    if sqs:
        try:
            from shared.queue.client import get_sqs_client

            get_sqs_client()
        except Exception as exc:
            logger.debug('warm sqs omitido: %s', type(exc).__name__)
    if lambda_:
        try:
            import shared.aws.lambda_invoke as lambda_invoke

            # Materializa el cliente boto3 'lambda' (service model +
            # credenciales/endpoint) en INIT. El EXECUTE a 0.07 vCPU solo
            # reusa el singleton para el invoke async (InvocationType=Event).
            _ = lambda_invoke.lambda_client
        except Exception as exc:
            logger.debug('warm lambda omitido: %s', type(exc).__name__)
