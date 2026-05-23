# Fase 5 — Script de scan automatizado (devtools)

> Objetivo: `python devtools/run.py agent_readiness_scan --url=<URL>`
> ejecuta scan en isitagentready.com via Playwright headless y publica
> resultado JSON. Cubre AC-13, AC-14 (verificacion del score >= 70).

## 1. Por que scraping y no API

isitagentready.com **no tiene API publica documentada** (verificado el
22-May-2026 con devtools del browser: la web hace requests a su backend
interno con cookies de sesion, no expone endpoint REST estable).

Opciones evaluadas:
- Llamar a Cloudflare Workers AI internamente — requiere API key
- Reimplementar el scan (re-scrap los 33 checks) — costo alto, divergencia
- **Scraping con Playwright** — usa el scan oficial, parsing del DOM

Se elige la 3era. Playwright ya esta como devdep para tests E2E del
portfolio (`tests/feature/`). El script se trata como "test estructural"
y publica un JSON con la breakdown.

## 2. Estructura del script

```text
devtools/agent_readiness_scan/
├── __init__.py
├── main.py              # entry point: main(flags: dict)
├── flags.py             # parsing y validacion de flags
├── scanner.py           # logica Playwright (open page, fill URL, wait, parse)
├── parser.py            # extrae score + breakdown del DOM
├── reporter.py          # genera JSON / stdout
└── README.md
```

Tests: `devtools/tests/agent_readiness_scan/test_parser_extracts_score.py`,
etc. (parser es pura, testeable sin Playwright).

## 3. Comportamiento esperado

```bash
# Scan basico
python devtools/run.py agent_readiness_scan --url=https://stage.the-full-stack.com

# Output JSON estructurado
python devtools/run.py agent_readiness_scan \
  --url=https://stage.the-full-stack.com \
  --output=docs/progress/agent_readiness_$(date +%s).json

# Scan multiple URLs (los 6 subdominios)
python devtools/run.py agent_readiness_scan \
  --url=https://stage.the-full-stack.com \
  --url=https://hub.portfolio.stage.the-full-stack.com \
  --url=https://fintech.portfolio.stage.the-full-stack.com \
  --url=https://architect.portfolio.stage.the-full-stack.com \
  --url=https://leader.portfolio.stage.the-full-stack.com \
  --url=https://vibe.portfolio.stage.the-full-stack.com

# Verificacion: exit 0 si score >= --min-score, 1 si menor
python devtools/run.py agent_readiness_scan \
  --url=https://stage.the-full-stack.com \
  --min-score=70
```

## 4. `main.py`

```python
"""Entry point del scan."""
import json
import logging
import sys

from .flags import parse_flags
from .reporter import print_summary, write_json
from .scanner import scan_url

logger = logging.getLogger(__name__)


def main(flags: dict) -> int:
    urls = flags['urls']
    output_path = flags.get('output')
    min_score = flags.get('min_score')

    results = []
    for url in urls:
        logger.info('Scanning %s', url)
        result = scan_url(url=url, timeout=flags['timeout'])
        results.append(result)
        print_summary(result)

    if output_path:
        write_json(results=results, path=output_path)

    # Verificacion del score minimo
    if min_score is not None:
        below = [r for r in results if r['score'] < min_score]
        if below:
            logger.error('Score below threshold for %d URL(s): %s',
                         len(below), [(r['url'], r['score']) for r in below])
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main(parse_flags()))
```

## 5. `scanner.py`

Playwright headless. La web del scanner tiene un input para la URL,
boton "scan" y muestra resultados despues de ~5-15s.

```python
"""Scanner: abre isitagentready.com, ejecuta el scan, devuelve raw HTML."""
from playwright.sync_api import sync_playwright

SCANNER_URL = 'https://isitagentready.com'
DEFAULT_TIMEOUT = 60_000  # ms — el scan toma ~10-15s, damos margen


def scan_url(*, url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto(SCANNER_URL, timeout=timeout)
            # Llenar input con la URL
            page.fill('input[type="url"]', url)
            page.click('button:has-text("Scan")')
            # Esperar que aparezca el score (el DOM tiene un elemento .score-card)
            page.wait_for_selector('[data-testid="score-card"]', timeout=timeout)
            html = page.content()
            from .parser import parse_results
            parsed = parse_results(html=html, url=url)
            return parsed
        finally:
            browser.close()
```

## 6. `parser.py`

Selectores CSS basados en el DOM observado del scan (capturado el
22-May-2026). Si el sitio cambia su layout, ajustar selectores.

```python
"""Parser: extrae score + breakdown del HTML del scanner."""
import re
from bs4 import BeautifulSoup
from dataclasses import dataclass


@dataclass
class CategoryScore:
    name: str
    points: int
    max_points: int


def parse_results(*, html: str, url: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')

    # Score total (ej: "33")
    score_el = soup.select_one('[data-testid="score-total"]')
    total = int(score_el.get_text(strip=True)) if score_el else 0

    # Categorias y puntos por categoria
    categories = []
    for cat_el in soup.select('[data-testid="category-card"]'):
        name = cat_el.select_one('[data-testid="category-name"]').get_text(strip=True)
        score_text = cat_el.select_one('[data-testid="category-score"]').get_text(strip=True)
        # 'X/Y' -> (X, Y)
        m = re.match(r'(\d+)\s*/\s*(\d+)', score_text)
        if m:
            categories.append(CategoryScore(
                name=name, points=int(m.group(1)), max_points=int(m.group(2)),
            ))

    return {
        'url': url,
        'score': total,
        'categories': [
            {'name': c.name, 'points': c.points, 'max_points': c.max_points}
            for c in categories
        ],
        'timestamp': _now_iso(),
    }


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
```

> Los selectores `[data-testid="..."]` son **suposiciones razonables**.
> Antes de implementar, abrir el scanner real, inspeccionar el DOM y
> ajustar a los atributos verdaderos. Si el DOM no tiene `data-testid`,
> fallback a selectores por texto/clase. Documentar los selectores
> elegidos como **"fragil — re-validar tras cualquier change UI del
> scanner"**.

## 7. `reporter.py`

```python
"""Reporta resultados a stdout (resumen) y JSON (auditable)."""
import json
from pathlib import Path


def print_summary(result: dict) -> None:
    score = result['score']
    level = _level_for_score(score)
    print(f'\n=== {result["url"]} ===')
    print(f'Score: {score}/100 — {level}')
    print('Categorias:')
    for cat in result['categories']:
        print(f'  {cat["name"]}: {cat["points"]}/{cat["max_points"]}')


def write_json(*, results: list, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(f'\nJSON guardado en: {path}')


def _level_for_score(score: int) -> str:
    if score >= 90: return 'Level 5 Fully Agent-Ready'
    if score >= 70: return 'Level 4 Agent-Ready'
    if score >= 50: return 'Level 3 Agent-Aware'
    if score >= 30: return 'Level 2 Bot-Aware'
    return 'Level 1 Not Ready'
```

## 8. `flags.py`

```python
"""Parsing y validacion de flags."""
import argparse
import sys


def parse_flags(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description='Agent Readiness scan via isitagentready.com')
    parser.add_argument('--url', action='append', required=True,
                        help='URL a escanear (repetible)')
    parser.add_argument('--output', help='Path para volcar JSON (opcional)')
    parser.add_argument('--min-score', type=int, default=None,
                        help='Si se provee, exit 1 cuando algun score < min-score')
    parser.add_argument('--timeout', type=int, default=60_000,
                        help='Timeout ms por scan (default 60000)')
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    return {
        'urls': args.url,
        'output': args.output,
        'min_score': args.min_score,
        'timeout': args.timeout,
    }
```

## 9. `README.md` del modulo

```markdown
# agent_readiness_scan

Script que ejecuta el scan oficial de isitagentready.com via Playwright
headless y devuelve el score + breakdown como JSON.

## Uso

\`\`\`bash
# scan basico
python devtools/run.py agent_readiness_scan --url=https://the-full-stack.com

# multiple URLs con output JSON
python devtools/run.py agent_readiness_scan \\
  --url=https://stage.the-full-stack.com \\
  --url=https://hub.portfolio.stage.the-full-stack.com \\
  --output=docs/progress/agent_readiness_stage_$(date +%s).json

# como gate de CI
python devtools/run.py agent_readiness_scan \\
  --url=https://stage.the-full-stack.com \\
  --min-score=70
\`\`\`

## Dependencias

- Playwright (devdep ya instalada para tests/feature)
- BeautifulSoup4 (agregar a devtools/pyproject.toml)
\`\`\`

## 10. Tests del modulo

`devtools/tests/agent_readiness_scan/test_parser_extracts_score.py`:

```python
"""Given HTML del scanner con score 33, When parse_results, Then dict
con score=33 y categorias parseadas."""
from agent_readiness_scan.parser import parse_results

SAMPLE_HTML = '''
<div data-testid="score-total">33</div>
<div data-testid="category-card">
  <span data-testid="category-name">Discoverability</span>
  <span data-testid="category-score">2/3</span>
</div>
<div data-testid="category-card">
  <span data-testid="category-name">Bot Access Control</span>
  <span data-testid="category-score">2/2</span>
</div>
'''


def test_parser_extracts_total_score():
    # Arrange / Act
    result = parse_results(html=SAMPLE_HTML, url='https://x.com')
    # Assert
    assert result['score'] == 33
    assert result['url'] == 'https://x.com'


def test_parser_extracts_categories_with_points():
    # Arrange / Act
    result = parse_results(html=SAMPLE_HTML, url='https://x.com')
    # Assert
    assert len(result['categories']) == 2
    assert result['categories'][0] == {
        'name': 'Discoverability', 'points': 2, 'max_points': 3,
    }
    assert result['categories'][1] == {
        'name': 'Bot Access Control', 'points': 2, 'max_points': 2,
    }
```

`devtools/tests/agent_readiness_scan/test_flags_parsing.py`:

```python
"""Given args validos, When parse_flags, Then dict tipado."""
from agent_readiness_scan.flags import parse_flags


def test_parse_flags_single_url():
    result = parse_flags(['--url=https://x.com'])
    assert result['urls'] == ['https://x.com']
    assert result['min_score'] is None


def test_parse_flags_min_score():
    result = parse_flags(['--url=https://x.com', '--min-score=70'])
    assert result['min_score'] == 70
```

## 11. Agregar dep al devtools

```bash
cd devtools && uv add beautifulsoup4
# (playwright ya es devdep)
```

Verificar:

```bash
cat devtools/pyproject.toml | grep beautifulsoup
```

## 12. Verificacion incremental

```bash
# Tests unit del parser (no requiere navegador)
python devtools/run.py test_runner --module=devtools --type=unit

# Smoke test del scanner contra el portfolio actual (deberia dar 33-ish)
python devtools/run.py agent_readiness_scan --url=https://the-full-stack.com

# Despues de implementar fases 1-4 y deploy a stage:
python devtools/run.py agent_readiness_scan \
  --url=https://stage.the-full-stack.com \
  --min-score=70
```

## 13. Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| isitagentready.com cambia layout | Selectores fragiles; documentado en README. Tests unit del parser usan HTML fixture |
| Rate-limit del scanner si lo corremos repetido | Delay 5s entre URLs (`time.sleep(5)`) en el loop |
| Cloudflare bot challenge bloquea Playwright | Probar primero; si bloquea, agregar headers `user-agent` realistas o cookies de sesion previa |
| El scan no termina (timeout) | `--timeout=60000` por default; el script falla con exit 2 si timeout |

## 14. Notas

- El JSON de cada scan va a `docs/progress/agent_readiness_<ts>.json`,
  que esta en `.gitignore` (artefacto efimero — ver
  `.claude/rules/harness-protocol.md`).
- Para historial, el commit del PR mergeado incluye en su body un
  resumen del ultimo scan (no el JSON crudo).
- Este script NO se corre en CI. Es **manual post-deploy a stage**.
