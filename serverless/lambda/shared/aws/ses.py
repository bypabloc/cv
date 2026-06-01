"""@module shared.aws.ses — SES v2 (boto3.client('sesv2')) + helper send_email.

Decision (.claude/docs/aws-ses/01-architecture.md):
SES v2 API recomendada en 2026, v1 deprecated. v2 expone SendEmail con
mejor manejo de bounce/complaint y soporte para email identities como
domain identity (no email-by-email).

API publica:

- `ses` — cliente sesv2 LAZY (PEP 562 `__getattr__` a nivel de modulo). NO
  se instancia en el import: el primer acceso a `shared.aws.ses.ses` lo
  crea. Asi un Lambda que importa `shared.aws` (por ssm/dynamodb) pero
  NUNCA manda email no paga la creacion del cliente SES en el cold start.
- `send_email(...)` — helper de alto nivel que arma el payload
  `{Content.Simple.{Subject, Body.{Text, Html}}, Destination, ReplyToAddresses}`
  y delega en un cliente lazy (compat con moto en tests). Es el patron
  que el `core/` de los services debe usar (NO `import boto3`).
"""

from __future__ import annotations

import os
from typing import Any


def _client() -> Any:
    """Devuelve un cliente sesv2 nuevo (lazy, compat con moto).

    SES domain identity esta en us-east-1 (SPEC-000 + SPEC-011). Se fuerza
    el region para evitar el default boto3 que podria leer
    `AWS_REGION=us-east-1` pero terminar pegando a us-west-2 sandbox.
    """
    import boto3  # lazy: boto3 NO se importa al cargar el modulo

    return boto3.client(
        'sesv2', region_name=os.environ.get('AWS_SES_REGION', 'us-east-1')
    )


def __getattr__(name: str) -> Any:
    """PEP 562: `shared.aws.ses.ses` crea el cliente al primer acceso."""
    if name == 'ses':
        return _client()
    msg = f"module 'shared.aws.ses' has no attribute '{name}'"
    raise AttributeError(msg)


def send_email(
    *,
    from_address: str,
    to_addresses: list[str],
    subject: str,
    text_body: str,
    html_body: str | None = None,
    reply_to: list[str] | None = None,
) -> dict[str, Any]:
    """Envia un email via SES v2.

    Encapsula el patron `boto3.client('sesv2').send_email(...)` para que
    los `core/` de los services no necesiten `import boto3`. El cliente es
    lazy (no module-scope) para que moto lo intercepte en tests.

    Parameters
    ----------
    from_address : str
        From address verificado en SES (formato `Name <addr@domain>` o
        `addr@domain` plano).
    to_addresses : list[str]
        Lista de destinatarios principales.
    subject : str
        Asunto del email.
    text_body : str
        Cuerpo plano (obligatorio para deliverability — los clientes que
        no renderizan HTML caen aqui).
    html_body : str | None
        Cuerpo HTML opcional. Si se provee, el email es multipart.
    reply_to : list[str] | None
        Reply-To addresses opcionales.

    Returns
    -------
    dict[str, Any]
        Response de SES v2 (incluye `MessageId`).
    """
    body: dict[str, Any] = {
        'Text': {'Data': text_body, 'Charset': 'UTF-8'},
    }
    if html_body is not None:
        body['Html'] = {'Data': html_body, 'Charset': 'UTF-8'}

    request: dict[str, Any] = {
        'FromEmailAddress': from_address,
        'Destination': {'ToAddresses': to_addresses},
        'Content': {
            'Simple': {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': body,
            },
        },
    }
    if reply_to:
        request['ReplyToAddresses'] = reply_to

    return _client().send_email(**request)
