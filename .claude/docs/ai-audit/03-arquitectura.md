# 03 - Arquitectura interna

> Como esta organizado `devtools/ai_audit/`, contratos entre modulos,
> decisiones de diseno.

[< 02 Auth](02-auth-setup.md) | [04 Troubleshooting >](04-troubleshooting.md)

## Estructura del paquete

```text
devtools/ai_audit/
├── __init__.py            # re-exports
├── README.md              # uso interno + cuando partir un archivo
├── main.py                # def main(flags: dict) -> int   (entry)
├── flags.py               # parsing + validacion de flags
├── catalog.py             # niche -> URL por env (los 6 sitios)
├── auth.py                # load + setup storageState
├── scraper.py             # Playwright runner + retry/backoff
├── tools/
│   ├── __init__.py        # registry: name -> tool module
│   ├── base.py            # contract: ToolResult dataclass + parse()
│   ├── isitagentready.py
│   ├── aibotchecker.py
│   ├── ahrefs.py
│   └── semrush.py
├── report.py              # snapshot JSON + Markdown render
└── tmp/                   # ignored — solo doc del runtime layout
```

Restricciones (per `.claude/rules/python.md`):

- Max 300 lineas por archivo.
- Type hints obligatorios en funciones publicas.
- Ruff config heredada de `devtools/ruff.toml`.

## Contratos clave

### `ToolResult` (dataclass)

```python
@dataclass(frozen=True)
class ToolResult:
    tool: str            # 'isitagentready' | 'aibotchecker' | 'ahrefs' | 'semrush'
    target: str          # URL absoluta auditada
    status: Status       # OK | PARTIAL | BLOCKED | ERROR | SKIPPED
    score: int | None    # 0-100 (None si BLOCKED/ERROR/SKIPPED)
    categories: dict[str, int | str]  # depende del tool
    fixes: list[Fix]     # max 5, ya ordenados por severidad
    raw_log_path: Path   # ruta al log Playwright
    duration_ms: int
```

### `Fix` (dataclass)

```python
@dataclass(frozen=True)
class Fix:
    severity: Severity   # high | medium | low
    category: str        # nombre de la categoria del tool
    issue: str           # descripcion del problema (1 linea)
    fix: str             # accion concreta (copy-paste si el tool la da)
    file: str | None     # archivo del repo a tocar (si se puede inferir)
    reach: int           # cuantos crawlers afecta (0-10)
```

### Contrato de `tools/<name>.py`

Cada tool implementa:

```python
TOOL_NAME = 'isitagentready'
REQUIRES_AUTH = False
BASE_URL = 'https://isitagentready.com'

async def scrape(page: Page, target: str) -> ToolResult:
    """Ejecuta el audit y parsea el resultado."""
```

`scraper.py` itera el registry, llama `scrape()` con retry, agrega al
snapshot.

## Flow del orquestador

```text
main(flags)
  -> validate_flags(flags)
  -> resolve_targets(env, niches, targets_override)  # via catalog.py
  -> select_tools(tools_flag, available_auth)         # via auth.py
  -> playwright_run(targets x tools):
       for target in targets:
         for tool in tools:
           with retry(3, backoff=[5, 15, 45]):
             result = tool.scrape(page, target)
           snapshot.append(result)
           sleep(5)  # entre tools
         sleep(2)  # entre targets
  -> snapshot.write_json(tmp/ai-audit/<ts>/snapshot.json)
  -> report.render_markdown(snapshot, tmp/ai-audit/<ts>/report.md)
  -> print summary table + path al report
  -> exit code:
       0 = todos OK o PARTIAL
       1 = >= 50% BLOCKED/ERROR
       2 = error interno (config invalida, playwright no instalado)
```

## Decisiones de diseno

### Playwright Python (no Node, no docker)

Razon: devtools es Python autocontenido. Playwright Python via
`uv add playwright` mantiene el patron y evita orquestar Docker para
un script CLI.

Trade-off: ~280MB extra en `devtools/.venv` por chromium. Se descarga
una sola vez con `playwright install chromium` (idempotente — el
script lo invoca en el primer run si falta).

### Anonimo vs storageState por tool

Las 4 tools tienen comportamiento mixto. Para no acoplar el scraper
al modo auth, cada tool declara `REQUIRES_AUTH: bool`. El orquestador
elige el contexto Playwright correcto:

```python
if tool.REQUIRES_AUTH:
    context = browser.new_context(storage_state=auth.load(tool.TOOL_NAME))
else:
    context = browser.new_context()  # incognito
```

Asi un mismo run audita las 4 sin mezclar sesiones.

### Retry policy

- `tenacity` (ya transitivo) — wait_exponential(5, 45), stop_after_attempt(3).
- Solo reintenta ante: TimeoutError, network 5xx, presencia de
  `cf-challenge-form` en DOM, response 429.
- NO reintenta ante: 401/403 logicos (auth invalida), 404 (URL mal
  formada), parse errors deterministas (DOM cambio).

### Snapshot inmutable

`snapshot.json` se escribe UNA vez al final. Si el run se interrumpe
(Ctrl-C), se escribe lo capturado hasta el momento + marca de
`interrupted: true` en metadata. Asi un run cancelado no pierde
trabajo.

### Reporte Markdown

Renderizado a partir del JSON. Se puede re-generar de un snapshot
viejo con `ai_audit report --snapshot=<path>`. Util para iterar el
formato del reporte sin re-scrapear.

## Tests

```text
devtools/tests/unit/src/ai_audit/
├── test_flags.py            # parsing + validacion
├── test_catalog.py          # niche -> URL por env
├── test_auth.py             # load + check_only (mockea Playwright)
├── test_scraper.py          # retry policy, sleep entre tools
├── test_report.py           # render Markdown + prioritization
└── tools/
    ├── test_isitagentready.py  # parse() sobre HTML fixture
    ├── test_aibotchecker.py
    ├── test_ahrefs.py
    └── test_semrush.py
```

Fixtures HTML capturados de runs reales en
`devtools/tests/unit/src/ai_audit/fixtures/<tool>/<scenario>.html`
(commiteables — son outputs publicos sin info sensible).

Coverage: >= 80% per-file. Mockear Playwright (`Page` mock); NUNCA
hacer red en unit tests.

[< 02 Auth](02-auth-setup.md) | [04 Troubleshooting >](04-troubleshooting.md)
