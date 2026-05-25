# 04 - Fase tools (4 scrapers)

> Implementacion de los 4 modulos en `devtools/ai_audit/tools/`. Cada
> uno es independiente y paralelizable (1 archivo, 1 test file, 1
> fixture HTML). Maximo aprovechamiento de git worktrees.

[< 03 Auth](03-fase-auth.md) | [05 Report >](05-fase-report.md)

## Alcance

- `tools/base.py` con `ToolResult`, `Fix`, `Status`, `Severity`,
  `Tool` protocol.
- `tools/__init__.py` con registry `REGISTRY: dict[str, Tool]`.
- `tools/isitagentready.py`, `aibotchecker.py`, `ahrefs.py`,
  `semrush.py` — uno por tool.
- Fixture HTML por tool en
  `devtools/tests/unit/src/ai_audit/fixtures/<tool>/sample.html`.
- Tests por tool con asserts EXACTOS.

## AC referenciados

- AC-2 (1 audit OK con score, categorias, fixes)
- AC-6 (SKIPPED si auth requerido sin storageState)
- AC-9 (coverage >= 80% per-file)

## Tareas atomicas

### T-4.1 base.py contratos

```python
class Status(StrEnum):
    OK = 'OK'
    PARTIAL = 'PARTIAL'
    BLOCKED = 'BLOCKED'
    ERROR = 'ERROR'
    SKIPPED = 'SKIPPED'

class Severity(StrEnum):
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

@dataclass(frozen=True)
class Fix:
    severity: Severity
    category: str
    issue: str
    fix: str
    file: str | None
    reach: int  # 0-10

@dataclass(frozen=True)
class ToolResult:
    tool: str
    target: str
    status: Status
    score: int | None
    categories: dict[str, int | str]
    fixes: tuple[Fix, ...]
    raw_log_path: Path
    duration_ms: int
    skipped_reason: str | None = None

class Tool(Protocol):
    TOOL_NAME: str
    REQUIRES_AUTH: bool
    BASE_URL: str

    async def scrape(self, page: 'Page', target: str) -> ToolResult: ...
```

**Verify**: `python -m compileall -q devtools/ai_audit/tools/base.py`.

### T-4.2 Cada tool (paralelizable, ver fase 09)

Para cada tool, mismo patron:

1. Capturar fixture HTML real corriendo el audit en browser y
   guardando el HTML resultado.
2. Implementar `scrape(page, target)`:
   - `page.goto(BASE_URL)`
   - Llenar input con `target`
   - Click submit
   - Esperar selector de resultado (`page.wait_for_selector(...)`)
   - Parsear DOM (BeautifulSoup o Playwright selectors)
   - Construir `ToolResult`
3. Tests:
   - Cargar fixture HTML, parsear, assertear score / categorias /
     fixes EXACTOS [AC-2].
   - Mock para flujo BLOCKED (challenge en DOM) [AC-4 parcial].

#### isitagentready.py

- `TOOL_NAME='isitagentready'`, `REQUIRES_AUTH=False`,
  `BASE_URL='https://isitagentready.com'`.
- Parser: extrae score 0-100 + 5 categorias + top 5 fixes con
  recomendacion copy-paste.
- Selectores (al momento del fixture): `[data-test='score-value']`,
  `[data-test='category-row']`, `[data-test='fix-item']`. Pueden
  cambiar (ver troubleshooting).

#### aibotchecker.py

- `REQUIRES_AUTH=False`. Tabla per-agent (GPTBot, ClaudeBot, etc.)
  con status allow/block.
- Score agregado = % de bots que SI tienen acceso correcto.
- Fixes derivados de las filas con status=block.

#### ahrefs.py

- `REQUIRES_AUTH=True`. Login URL en `auth.LOGIN_URLS['ahrefs']`.
- Score = nro de plataformas IA donde el dominio aparece.
- Categorias = dict por plataforma (ChatGPT, Gemini, Perplexity,
  Copilot, Google AI Overviews) con nro de mentions.
- Si `auth.check('ahrefs') != VALID`: retornar `ToolResult` con
  `status=SKIPPED, skipped_reason='storageState missing'` [AC-6].

#### semrush.py

- Idem ahrefs en estructura. Score 0-100. Categorias: Technical,
  Content, Visibility.

### T-4.3 Registry

```python
# tools/__init__.py
from .isitagentready import IsItAgentReady
from .aibotchecker import AiBotChecker
from .ahrefs import Ahrefs
from .semrush import Semrush

REGISTRY = {
    'isitagentready': IsItAgentReady(),
    'aibotchecker': AiBotChecker(),
    'ahrefs': Ahrefs(),
    'semrush': Semrush(),
}
```

### T-4.4 Tests por tool

`test_<tool>.py`:

- Given fixture `<tool>/sample.html`, When `parse_dom(html)`, Then `score==<exact>` [AC-2]
- Given fixture `<tool>/sample.html`, When `parse_dom(html)`, Then `categories=={"Discoverability": 90, ...}` (dict literal) [AC-2]
- Given fixture `<tool>/sample.html`, When `parse_dom(html)`, Then `len(fixes)==5` y `fixes[0].severity==Severity.HIGH` [AC-2]
- Given fixture con challenge `<tool>/challenge.html`, When `parse_dom`, Then raises `BlockedError` [AC-4]
- (solo Ahrefs/Semrush) Given auth.check -> MISSING, When `scrape`, Then retorna `status=SKIPPED` sin abrir browser [AC-6]

Mockear `Page` con `unittest.mock`; alimentar fixtures via
`page.content()` mockeado.

## Done

- [ ] T-4.1 base.py + types: compileall ok
- [ ] T-4.2 4 scrapers: implementacion + fixtures HTML capturados
- [ ] T-4.3 registry expuesto
- [ ] T-4.4 tests: 5+ tests por tool, coverage >= 80% per-file
- [ ] Commits (4 paralelizables): uno por tool

  - `feat(devtools): ai_audit tool isitagentready (parser + tests)`
  - `feat(devtools): ai_audit tool aibotchecker (parser + tests)`
  - `feat(devtools): ai_audit tool ahrefs (auth-gated parser + tests)`
  - `feat(devtools): ai_audit tool semrush (auth-gated parser + tests)`

## Notas para paralelizacion

Los 4 archivos `tools/<X>.py` y sus tests son FILE-EXCLUSIVE — un
worktree por tool sin colision. `tools/__init__.py` (registry) se
toca al final por el orquestador para evitar conflicto de imports.

Ver [09-paralelizacion-worktrees.md](09-paralelizacion-worktrees.md).

[< 03 Auth](03-fase-auth.md) | [05 Report >](05-fase-report.md)
