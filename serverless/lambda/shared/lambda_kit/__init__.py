"""Subpaquete `lambda_kit`: Kit comun del estandar lambda-controller.

Subpaquete SIN barrel: este `__init__` NO re-exporta nada. Importar
SIEMPRE del modulo concreto (contrato `.claude/rules/lambda-shared-imports.md`):

    from shared.lambda_kit.http_dispatch import http_handler
    from shared.lambda_kit.base_controller import BaseController
"""
