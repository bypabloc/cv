"""Base types y protocol que todas las tools del ai_audit implementan."""

from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum
from pathlib import Path
from typing import Any
from typing import Protocol
from typing import runtime_checkable


class Status(StrEnum):
    """Resultado de un audit por (target, tool)."""

    OK = 'OK'
    PARTIAL = 'PARTIAL'
    BLOCKED = 'BLOCKED'
    ERROR = 'ERROR'
    SKIPPED = 'SKIPPED'


class Severity(StrEnum):
    """Severidad de un fix recomendado."""

    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


@dataclass(frozen=True)
class Fix:
    """Una recomendacion accionable extraida del resultado del audit."""

    severity: Severity
    category: str
    issue: str
    fix: str
    file: str | None = None
    reach: int = 1


@dataclass(frozen=True)
class ToolResult:
    """Resultado de auditar UN target con UNA tool."""

    tool: str
    target: str
    status: Status
    score: int | None
    categories: dict[str, int | str] = field(default_factory=dict)
    fixes: tuple[Fix, ...] = ()
    raw_log_path: Path | None = None
    duration_ms: int = 0
    skipped_reason: str | None = None
    error_message: str | None = None


class BlockedError(Exception):
    """Lanzada por un scraper cuando detecta un challenge / rate-limit."""


class ParseError(Exception):
    """Lanzada por un scraper cuando el DOM no matchea los selectores."""


@runtime_checkable
class Tool(Protocol):
    """Protocol que implementa cada tool concreta."""

    TOOL_NAME: str
    REQUIRES_AUTH: bool
    BASE_URL: str

    async def scrape(self, page: Any, target: str) -> ToolResult:
        """Ejecuta el audit + parsea el resultado."""
        ...

    def parse_dom(self, html: str, target: str) -> ToolResult:
        """Pure parsing helper: extrae datos del HTML capturado.

        Permite testear el parser sin Playwright (con fixtures HTML).
        """
        ...
