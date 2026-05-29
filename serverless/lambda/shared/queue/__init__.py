"""Subpaquete `queue`: Publisher SQS para los encoders.

Subpaquete SIN barrel: este `__init__` NO re-exporta nada. Importar
SIEMPRE del modulo concreto (contrato `.claude/rules/lambda-shared-imports.md`):

    from shared.queue.publisher import send_to_queue
"""
