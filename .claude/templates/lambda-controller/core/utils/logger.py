"""
Logger estructurado para el servicio Lambda.

Emite logs JSON a stdout (capturado por CloudWatch). Sin dependencias
externas: reemplaza a librerias propietarias tipo `bifrost.logger`.
Para un setup mas completo (tracer, metrics) considerar AWS Lambda
Powertools v3.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

import json
import logging
import os
import sys
from typing import Any

_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


class Logger:
    """
    Logger JSON estructurado para Lambda.

    Cada llamada emite una linea JSON con message, level, extra y los
    campos del contexto cargado via basic_loader.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
    """

    def __init__(self, *context_keys: str) -> None:
        self._level = _LEVELS.get(
            os.environ.get('LOG_LEVEL', 'INFO').upper(),
            logging.INFO,
        )
        self._context_keys = context_keys
        self._context: dict[str, Any] = {}

    def basic_loader(self, **kwargs: Any) -> None:
        """Carga campos de contexto que se adjuntan a cada log."""
        for key in self._context_keys:
            if key in kwargs:
                self._context[key] = kwargs[key]

    def _emit(
        self,
        level_name: str,
        message: str,
        *,
        extra: dict[str, Any] | None = None,
        exception: BaseException | None = None,
    ) -> None:
        if _LEVELS[level_name] < self._level:
            return
        record: dict[str, Any] = {
            'level': level_name,
            'message': message,
            **self._context,
        }
        if extra:
            record['extra'] = extra
        if exception is not None:
            record['exception'] = repr(exception)
        stream = sys.stderr if _LEVELS[level_name] >= logging.ERROR else sys.stdout
        print(json.dumps(record, default=str), file=stream)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log nivel DEBUG."""
        self._emit('DEBUG', message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log nivel INFO."""
        self._emit('INFO', message, **kwargs)

    def success(self, message: str, **kwargs: Any) -> None:
        """Log de exito (nivel INFO con marca)."""
        self._emit('INFO', message, **kwargs)

    def warn(self, message: str, **kwargs: Any) -> None:
        """Log nivel WARNING."""
        self._emit('WARNING', message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Alias de warn."""
        self._emit('WARNING', message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log nivel ERROR."""
        self._emit('ERROR', message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log nivel CRITICAL."""
        self._emit('CRITICAL', message, **kwargs)
