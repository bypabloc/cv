"""Registry de tools. Cada tool concreta se registra aqui.

El orquestador (ai_audit.scraper) usa REGISTRY para iterar y llamar
``scrape()`` en cada tool elegida por el usuario.

Tools activas:
- isitagentready  : API JSON publica de Cloudflare (anonima)
- validators      : validadores OSS propios (llms.txt, robots, sitemap, JSON-LD)
- lighthouse_psi  : Google PageSpeed Insights API (key gratis)
"""

from ai_audit.tools.base import BlockedError
from ai_audit.tools.base import Fix
from ai_audit.tools.base import ParseError
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.base import Tool
from ai_audit.tools.base import ToolResult
from ai_audit.tools.isitagentready import IsItAgentReady
from ai_audit.tools.lighthouse_psi import LighthousePsi
from ai_audit.tools.validators import Validators


REGISTRY: dict[str, Tool] = {
    'isitagentready': IsItAgentReady(),
    'validators': Validators(),
    'lighthouse_psi': LighthousePsi(),
}


__all__ = [
    'REGISTRY',
    'BlockedError',
    'Fix',
    'IsItAgentReady',
    'LighthousePsi',
    'ParseError',
    'Severity',
    'Status',
    'Tool',
    'ToolResult',
    'Validators',
]
