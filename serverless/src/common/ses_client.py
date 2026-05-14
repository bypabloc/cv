"""
SES v2 Client (boto3.client('sesv2')).

Decision (.claude/docs/aws-ses/01-architecture.md):
SES v2 API recomendada en 2026, v1 deprecated. v2 expone SendEmail con
mejor manejo de bounce/complaint y soporte para email identities como
domain identity (no email-by-email).

Module-scope para reusar HTTPS connection entre invocaciones warm.

Uso:
    from common.ses_client import ses

    ses.send_email(
        FromEmailAddress='no-reply@the-full-stack.com',
        Destination={'ToAddresses': ['owner@example.com']},
        Content={'Simple': {
            'Subject': {'Data': 'Test'},
            'Body': {'Text': {'Data': 'Hello'}, 'Html': {'Data': '<p>Hello</p>'}},
        }},
    )
"""

from __future__ import annotations

import os

import boto3

# SES domain identity esta en us-east-1 (SPEC-000 + SPEC-011). Forzamos
# el region para evitar default boto3 que podria leer AWS_REGION=us-east-1
# del template pero terminar pegando a us-west-2 sandbox.
ses = boto3.client(
    'sesv2',
    region_name=os.environ.get('AWS_SES_REGION', 'us-east-1'),
)
