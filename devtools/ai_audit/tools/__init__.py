"""Registry de tools. Las tools concretas se registran aqui despues
de C4-C7 (un archivo por tool).

El orquestador (ai_audit.scraper) usa REGISTRY para iterar y llamar
``scrape()`` en cada tool elegida por el usuario.
"""

from ai_audit.tools.base import BlockedError
from ai_audit.tools.base import Fix
from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.base import Tool
from ai_audit.tools.base import ToolResult


REGISTRY: dict[str, Tool] = {}


__all__ = [
    'REGISTRY',
    'BlockedError',
    'Fix',
    'ParseError',
    'Severity',
    'Status',
    'Tool',
    'ToolResult',
]
