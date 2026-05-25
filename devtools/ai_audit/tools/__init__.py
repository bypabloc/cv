"""Registry de tools. Cada tool concreta se registra aqui.

El orquestador (ai_audit.scraper) usa REGISTRY para iterar y llamar
``scrape()`` en cada tool elegida por el usuario.
"""

from ai_audit.tools.ahrefs import Ahrefs
from ai_audit.tools.aibotchecker import AiBotChecker
from ai_audit.tools.base import BlockedError
from ai_audit.tools.base import Fix
from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.base import Tool
from ai_audit.tools.base import ToolResult
from ai_audit.tools.isitagentready import IsItAgentReady
from ai_audit.tools.semrush import Semrush


REGISTRY: dict[str, Tool] = {
    'isitagentready': IsItAgentReady(),
    'aibotchecker': AiBotChecker(),
    'ahrefs': Ahrefs(),
    'semrush': Semrush(),
}


__all__ = [
    'REGISTRY',
    'Ahrefs',
    'AiBotChecker',
    'BlockedError',
    'Fix',
    'IsItAgentReady',
    'ParseError',
    'Semrush',
    'Severity',
    'Status',
    'Tool',
    'ToolResult',
]
