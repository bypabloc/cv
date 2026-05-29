"""Subpaquete `aws`: Clientes boto3 del backend: DynamoDB, SES v2, SSM, KMS.

Subpaquete SIN barrel: este `__init__` NO re-exporta nada. Importar
SIEMPRE del modulo concreto (contrato `.claude/rules/lambda-shared-imports.md`):

    from shared.aws.ssm import get_secret
    from shared.aws.dynamodb import get_table
"""
