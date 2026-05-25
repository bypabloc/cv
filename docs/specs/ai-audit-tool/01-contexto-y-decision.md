# 01 - Contexto y decision

[< README](README.md) | [02 Fase scaffold >](02-fase-scaffold.md)

## 1. Contexto / Problema

El portfolio busca aparecer en respuestas de ChatGPT, Claude,
Perplexity, Gemini, Copilot y Google AI Overviews (GEO — Generative
Engine Optimization). Hoy NO hay forma sistematica de medir que tan
preparado esta el sitio para crawlers de IA ni que cambios mueven la
aguja. La estrategia 2026 del skill `astro-portfolio` exige medicion
continua; sin metrica = no hay iteracion.

Existen 4 herramientas externas, cada una con un angulo distinto del
"AI readiness":

- **isitagentready.com** (Cloudflare, abril 2026): mide adopcion de
  standards emergentes para agentes (MCP, robots.txt Content
  Signals, Markdown negotiation).
- **aibotchecker.online** (independiente): mide accesibilidad real
  per-bot (GPTBot, ClaudeBot, etc.) con 60+ checks tecnicos.
- **Ahrefs AI Visibility Checker**: mide presencia/citacion de marca
  en respuestas reales de ChatGPT, Gemini, Perplexity, Copilot.
- **Semrush AI Visibility Audit**: combina technical + content +
  trafico real desde plataformas IA.

Ninguna tiene API publica gratuita. La unica via es scraping headless
del frontend.

### Hallazgos de exploracion

- Las 4 son free (Ahrefs + Semrush requieren cuenta gratis).
- isitagentready + aibotchecker = anonimas; Ahrefs + Semrush =
  Playwright storageState (categoria `dev-cli`).
- dev/stage del portfolio bloquean AI crawlers por diseno (noindex,
  robots Disallow). Auditarlos da scores falsos negativos. El audit
  vale como gate sobre **prod**.
- Ya existe el patron `docker/env/dev-cli/` para credenciales
  personales del dev (IAM keys + API tokens), gitignored. El
  storageState entra ahi sin crear nueva categoria.
- devtools usa Python 3.14 + uv. Playwright Python via uv mantiene
  el patron sin meter Docker o Node nuevos.

## 2. Solucion propuesta

Crear un script `devtools/ai_audit` (paquete Python siguiendo el
patron de `devtools/<script>/`) que:

1. Lee flags: `--env`, `--niches`, `--targets`, `--tools`.
2. Resuelve la matriz `targets x tools` a auditar.
3. Lanza Playwright Python con un context por modo auth.
4. Por cada `(target, tool)`: scrape + parse + retry/backoff.
5. Persiste un `snapshot.json` + renderiza un `report.md` con
   ranking + top 5 fixes accionables.
6. Sale 0 (todo OK/PARTIAL), 1 (>= 50% BLOCKED/ERROR), 2 (config
   invalida).

Subcomandos:

- `setup --tool=<X>` — abre browser interactivo para guardar
  storageState.
- `report --snapshot=<path>` — re-renderiza el Markdown desde un
  snapshot existente.

Rule + skill + 4 docs viven en `.claude/` (ya entregados en commit 1
de este plan); el codigo se entrega en commits 2-N.

### Decisiones clave

- **Decision 1: Playwright Python en devtools/.venv** — Self-contained
  con el resto de devtools. Trade-off: 280MB de chromium se
  descargan en el primer run. Alternativa "reusar container feature"
  obligaba a Docker arriba para auditar; alternativa "container
  nuevo" duplicaba infra para 1 script.
- **Decision 2: storageState en `dev-cli`** — Es credencial personal;
  encaja con la categoria existente sin crear una nueva. Categoria
  `dev-cli` ya es LOCAL-ONLY, gitignored, NUNCA sincronizada a
  remoto (CI usa OIDC).
- **Decision 3: snapshot puntual, NO time-series** — MVP simple. Si
  surge demanda real de tracking historico, se agrega despues como
  fase opcional. Diferir evita scope creep ahora.
- **Decision 4: rule + skill + docs en commit 1, codigo despues** —
  Solicitud explicita del usuario. Riesgo: docs apuntan a comandos
  que aun no existen. Mitigacion: header "Estado" en cada archivo
  apuntando al plan; nadie corre comandos por accidente.
- **Decision 5: 4 tools independientes, fallo de una no aborta el
  run** — Cada scraper es un archivo aislado. El orquestador trata
  los resultados como tuplas; perder Ahrefs no invalida los otros 3.

## 3. Criterios de aceptacion

- **AC-1**: Given un dev en una maquina limpia, When corre
  `python devtools/run.py ai_audit setup --tool=ahrefs --check-only`,
  Then imprime `EXPIRED` o `MISSING` con exit 1 (sin storageState
  configurado) — no crashea.
- **AC-2**: Given prod accesible publicamente, When corre
  `python devtools/run.py ai_audit --tools=isitagentready
  --niches=generic`, Then en menos de 90s produce
  `tmp/ai-audit/<ts>/snapshot.json` con 1 resultado status=OK, score
  numerico, categorias dict y 0+ fixes.
- **AC-3**: Given un run completado, When el script termina, Then
  imprime una tabla resumen en stdout y el path absoluto al
  `report.md` generado.
- **AC-4**: Given una tool inaccesible (mock con 3x 503), When el
  scraper la encuentra, Then reintenta 3 veces con backoff [5, 15,
  45]s y luego registra `status=BLOCKED` en el snapshot — el run
  sigue con las demas tools sin abortar.
- **AC-5**: Given un snapshot existente, When corre
  `python devtools/run.py ai_audit report --snapshot=<path>`, Then
  re-renderiza el `report.md` sin re-scrapear (idempotente, < 5s).
- **AC-6**: Given un dev sin Ahrefs configurado, When corre
  `ai_audit --tools=ahrefs --niches=generic`, Then el snapshot
  contiene 1 resultado status=`SKIPPED` con razon
  `storageState missing`. Exit code 0 (no es error fatal).
- **AC-7**: Given flags invalidos (ej. `--tools=foo`), When invoca
  el script, Then exit code 2 con mensaje claro y NO crea carpeta
  `tmp/ai-audit/`.
- **AC-8**: Given el `playwright install chromium` no se corrio,
  When el primer run intenta abrir browser, Then el script lo
  ejecuta automaticamente, informa al usuario, y continua sin error.
- **AC-9**: Given tests unitarios del paquete `ai_audit`, When se
  ejecutan, Then 100% verde con coverage per-file >= 80%.
- **AC-10**: Given un dev que abre `.claude/skills/ai-audit/SKILL.md`,
  When lee la seccion "Estado", Then queda claro que la
  implementacion vive en `docs/specs/ai-audit-tool/` y los comandos
  funcionan solo tras mergear ese plan.

## 4. Diagrama de flujo

### Despues (no hay "antes" — feature nueva)

```text
[CLI] python devtools/run.py ai_audit --env=prod --niches=hub,fintech
   |
   v
[flags.py] validate -> dict
   |
   v
[catalog.py] resolve_targets(env, niches) -> [url1, url2]
   |
   v
[auth.py] select_tools(tools_flag) -> [(tool, has_auth?)]
   |
   v
[scraper.py] Playwright context per auth mode
   |
   +--> for each (target, tool):
   |       with retry([5, 15, 45]):
   |          tool.scrape(page, target) -> ToolResult
   |       append snapshot
   |       sleep(5) entre tools
   |    sleep(2) entre targets
   v
[snapshot.json] write to tmp/ai-audit/<ts>/
   |
   v
[report.py] render Markdown -> tmp/ai-audit/<ts>/report.md
   |
   v
stdout: tabla resumen + path al report
exit code: 0 | 1 | 2
```

## 5. Diagrama ER

N/A — no hay cambios en content collections del portfolio. Los
contratos internos (ToolResult, Fix) viven en
`devtools/ai_audit/tools/base.py` (ver
[03-arquitectura.md](../../.claude/docs/ai-audit/03-arquitectura.md)).

## 6. Tests requeridos

### 6.A. TDD flows (logica nueva)

- WHEN se valida `--tools=isitagentready,foo` THEN exit code 2 con
  mensaje `unknown tool: foo` [AC-7]
- WHEN se resuelve targets con `--env=prod --niches=hub` THEN
  retorna `['https://hub.portfolio.the-full-stack.com']` [AC-2]
- WHEN se ejecuta retry policy con 3x TimeoutError THEN dispara los
  3 waits [5, 15, 45]s en orden [AC-4]
- WHEN se renderiza `report.md` desde snapshot vacio THEN el archivo
  contiene encabezado + "no results" sin crashear [AC-5]

### 6.B. Unit tests (pytest)

- `devtools/tests/unit/src/ai_audit/test_flags.py` — parsing + validacion
- `test_catalog.py` — niche->URL por env
- `test_auth.py` — load + check_only (Playwright mockeado)
- `test_scraper.py` — retry policy, sleep entre tools
- `test_report.py` — render + prioritization de fixes
- `test_isitagentready.py` (+ 3 mas) — parse sobre HTML fixture

Coverage: >= 80% per-file. Asserts EXACTOS (NO rangos). Docstring
BDD (Given/When/Then). Ver `.claude/rules/python.md`.

### 6.C. Typecheck

- `ruff check devtools/ai_audit devtools/tests/unit/src/ai_audit`
- `python -m compileall -q devtools/ai_audit`

### 6.D. E2E

N/A en el sentido tradicional (no es feature de UI). El "E2E" para
este script es el smoke real en la fase 10: correr contra
isitagentready con un solo niche y verificar que produce snapshot
real + report renderizado.

## 7. Archivos afectados

### Crear

- `devtools/ai_audit/__init__.py` — package + re-exports
  - Verificar: `python -c "import sys; sys.path.insert(0, 'devtools'); from ai_audit import main"` sin error
- `devtools/ai_audit/main.py` — entry point `def main(flags)`
  - Verificar: `python -m compileall -q devtools/ai_audit/main.py`
- `devtools/ai_audit/flags.py` — parsing + validacion
  - Verificar: `pytest devtools/tests/unit/src/ai_audit/test_flags.py`
- `devtools/ai_audit/catalog.py` — niche -> URL por env
  - Verificar: `pytest .../test_catalog.py`
- `devtools/ai_audit/auth.py` — load + setup storageState
  - Verificar: `pytest .../test_auth.py`
- `devtools/ai_audit/scraper.py` — Playwright runner + retry
  - Verificar: `pytest .../test_scraper.py`
- `devtools/ai_audit/tools/__init__.py` — registry
- `devtools/ai_audit/tools/base.py` — `ToolResult`, `Fix`, `Status`, `Severity`
- `devtools/ai_audit/tools/isitagentready.py`
  - Verificar: `pytest .../tools/test_isitagentready.py`
- `devtools/ai_audit/tools/aibotchecker.py`
- `devtools/ai_audit/tools/ahrefs.py`
- `devtools/ai_audit/tools/semrush.py`
- `devtools/ai_audit/report.py` — JSON + Markdown
  - Verificar: `pytest .../test_report.py`
- `devtools/ai_audit/README.md`
- `devtools/tests/unit/src/ai_audit/*` — tests por modulo + fixtures HTML

### Modificar

- `devtools/pyproject.toml` — agregar `playwright` a `[project.dependencies]`
  - Verificar: `cd devtools && uv lock --check`
- `devtools/uv.lock` — regenerado por `uv lock`
- `devtools/run.py` — registrar el script en el plugin loader (si
  no es por convencion de nombre — confirmar al implementar)
- `.gitignore` raiz — agregar `tmp/ai-audit/` + `docker/env/dev-cli/ai-audit/`
  - Verificar: `git check-ignore tmp/ai-audit/test.json docker/env/dev-cli/ai-audit/ahrefs.json`

### Eliminar

N/A.

[< README](README.md) | [02 Fase scaffold >](02-fase-scaffold.md)
