"""
Powertools v3 Logger configurado.

Uso:
    from _shared.logger import logger

    @logger.inject_lambda_context
    def lambda_handler(event, context):
        logger.info('processing', extra={'request_id': context.aws_request_id})

El env var POWERTOOLS_SERVICE_NAME viene del SAM template Globals.
"""

from aws_lambda_powertools import Logger

# Configuracion via env vars (Globals.Function en template.yaml):
# - POWERTOOLS_SERVICE_NAME=portfolio-backend
# - POWERTOOLS_LOG_LEVEL={INFO,WARNING,DEBUG}
# - POWERTOOLS_LOGGER_LOG_EVENT (opcional, true loggea el event completo)
logger = Logger()
