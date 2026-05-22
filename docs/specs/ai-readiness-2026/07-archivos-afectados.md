# 07 — Archivos afectados

> Lista completa con verificacion explicita por archivo.

## Crear

### packages/seo (builders + data)

- `packages/seo/src/data/mcp-tools.ts` — fuente unica de las 4 tools MCP
  - Verificar: `pnpm --filter @portfolio/seo run typecheck` sin errores
  - Verificar: el tipo `McpTool` se exporta desde `packages/seo/src/index.ts`

- `packages/seo/src/data/api-base.ts` — resolver de URL API por stage
  - Verificar: `pnpm exec vitest run packages/seo/tests/unit/data/api-base.test.ts`

- `packages/seo/src/lib/build-api-catalog.ts` — builder del linkset RFC 9727
  - Verificar: `pnpm exec vitest run packages/seo/tests/unit/lib/build-api-catalog.test.ts`

- `packages/seo/src/lib/build-mcp-server-card.ts` — builder SEP-2127
  - Verificar: `pnpm exec vitest run packages/seo/tests/unit/lib/build-mcp-server-card.test.ts`

- `packages/seo/src/lib/build-agent-skills.ts` — builder agentskills.io RFC 0.2.0
  - Verificar: `pnpm exec vitest run packages/seo/tests/unit/lib/build-agent-skills.test.ts`

- Tests unit mirror: 5 archivos `.test.ts` en `packages/seo/tests/unit/{data,lib}/`
  - Verificar: coverage >= 80% per-file via `python devtools/run.py test_runner --module=pkg-seo --type=coverage`

### packages/app-shared (middleware + componente WebMCP)

- `packages/app-shared/src/middleware/ai-content.ts` — middleware Astro
  - Verificar: `pnpm exec vitest run packages/app-shared/tests/unit/middleware/ai-content.test.ts`

- `packages/app-shared/src/components/WebMCPRegistration.astro` — componente
  - Verificar: `pnpm --filter @portfolio/app-shared run typecheck`
  - Verificar: build de cualquier app importadora exitoso

- Tests unit en `packages/app-shared/tests/unit/{middleware,components}/`
  - Verificar: `python devtools/run.py test_runner --module=pkg-app-shared --type=coverage`

### apps/<app> (los 6 apps, mismo patron)

Para cada uno de `{generic, hub, fintech, architect, leader, vibe}`:

- `apps/<app>/src/pages/.well-known/api-catalog.ts`
  - Verificar: `pnpm --filter @portfolio/<app> run build && ls apps/<app>/dist/.well-known/api-catalog`

- `apps/<app>/src/pages/.well-known/mcp/server-card.json.ts`
  - Verificar: `pnpm --filter @portfolio/<app> run build && ls apps/<app>/dist/.well-known/mcp/server-card.json`

- `apps/<app>/src/pages/.well-known/agent-skills/index.json.ts`
  - Verificar: `pnpm --filter @portfolio/<app> run build && ls apps/<app>/dist/.well-known/agent-skills/index.json`

- `apps/<app>/src/middleware.ts` — re-export del middleware compartido
  - Verificar: build exitoso, archivo generado en `dist/_worker.js/`

### serverless/lambda/services/nlweb (Lambda nueva)

- `serverless/lambda/services/nlweb/manifest.yaml`
  - Verificar: `python devtools/run.py serverless deploy --lambda=nlweb --stage=dev --aws-profile=tfs-dev` (dry-run via `status` primero)

- `serverless/lambda/services/nlweb/pyproject.toml`
  - Verificar: `cd serverless/lambda/services/nlweb && uv sync --frozen`
  - Verificar: `python devtools/run.py serverless lint-deps --lambda=nlweb` sin errores

- `serverless/lambda/services/nlweb/uv.lock`
  - Verificar: generado al hacer `uv sync` (no se edita a mano)

- `serverless/lambda/services/nlweb/.gitignore` — excluye `build/`, `build.zip`, `__pycache__`
  - Verificar: `git status` no muestra `build/` tras hacer `serverless deploy`

- `serverless/lambda/services/nlweb/core/handler.py`
  - Verificar: `cd serverless/lambda/services/nlweb && uv run python -m compileall -q core`

- `serverless/lambda/services/nlweb/core/controllers/nlweb/__init__.py`
- `serverless/lambda/services/nlweb/core/controllers/nlweb/ask.py` — `Ask(BaseController)`
  - Verificar: import path correcto desde el handler (descubrimiento por convencion)

- `serverless/lambda/services/nlweb/core/services/retrieval_service.py`
- `serverless/lambda/services/nlweb/core/services/schema_org_service.py`
  - Verificar: ambos services testeados unit (>= 1 archivo de test por escenario)

- `serverless/lambda/services/nlweb/core/models/ask.py` — `AskPayload`
- `serverless/lambda/services/nlweb/core/models/schema_org.py`
  - Verificar: Pydantic schemas validados por mypy/pyright en CI

- `serverless/lambda/services/nlweb/core/settings/config.py`
- `serverless/lambda/services/nlweb/core/settings/operations.py`
  - Verificar: `OPERATIONS` define `nlweb` -> controller `nlweb`

- `serverless/lambda/services/nlweb/events/ask.json`
- `serverless/lambda/services/nlweb/events/ask_empty.json`
  - Verificar: `python devtools/run.py serverless run --stage=local --lambda=nlweb --event=events/ask.json` retorna 200

- Tests unit: minimo 10 archivos en `tests/unit/test_*.py` (uno por escenario)
  - Verificar: `python devtools/run.py serverless tests --type=unit --lambda=nlweb` verde
  - Verificar: coverage >= 80% via `--type=coverage`

- Tests integration en `tests/integration/test_ask_e2e_fintech_query_returns_real_data.py`
  - Verificar: `python devtools/run.py serverless tests --type=integration --lambda=nlweb`
  - Pre-requisito: Neon dev seedeado con el CV

### devtools/agent_readiness_scan

- `devtools/agent_readiness_scan/__init__.py`
- `devtools/agent_readiness_scan/main.py` — entry point
- `devtools/agent_readiness_scan/flags.py`
- `devtools/agent_readiness_scan/scanner.py` — Playwright
- `devtools/agent_readiness_scan/parser.py` — BeautifulSoup
- `devtools/agent_readiness_scan/reporter.py`
- `devtools/agent_readiness_scan/README.md`
  - Verificar: `python devtools/run.py agent_readiness_scan --url=https://example.com` corre sin error (puede dar score bajo, eso esta OK para smoke)

- Tests en `devtools/tests/agent_readiness_scan/test_parser_extracts_score.py`
- Tests en `devtools/tests/agent_readiness_scan/test_flags_parsing.py`
  - Verificar: `python devtools/run.py test_runner --module=devtools --type=unit`

### tests/feature (E2E Playwright)

- `tests/feature/specs/ai-readiness/well-known.spec.ts` — valida los 3 endpoints en las 6 apps
  - Verificar: stack local arriba + `python devtools/run.py test_runner --module=feature --type=feature --env=local`

- `tests/feature/specs/ai-readiness/content-negotiation.spec.ts` — markdown + Link headers
  - Verificar: idem arriba

- `tests/feature/specs/ai-readiness/webmcp.spec.ts` — WebMCP runtime
  - Verificar: idem; el test se skipea si el browser no tiene flag

## Modificar

### packages/seo

- `packages/seo/src/index.ts` — agregar exports de los 3 builders nuevos + `MCP_TOOLS` + `McpToolSchema` + `resolveApiBase`
  - Verificar: `pnpm --filter @portfolio/seo run typecheck`

### packages/app-shared

- `packages/app-shared/src/index.ts` — agregar export del componente `WebMCPRegistration` y del middleware `aiContentMiddleware`
  - Verificar: `pnpm --filter @portfolio/app-shared run typecheck`

- `packages/app-shared/package.json` — agregar `turndown` + `@types/turndown` a `devDependencies`
  - Verificar: `pnpm install --filter @portfolio/app-shared`

### apps/<app> (6 archivos por app)

- `apps/<app>/astro.config.ts` — agregar `@astrojs/cloudflare` adapter (mode: 'directory')
  - Verificar: `pnpm --filter @portfolio/<app> run build` y comprobar `dist/index.html` existe
  - Verificar: comprobar `dist/_worker.js/` existe con el middleware

- `apps/<app>/package.json` — agregar `@astrojs/cloudflare` a `devDependencies`
  - Verificar: `pnpm install --filter @portfolio/<app>`

- `apps/<app>/src/layouts/BaseLayout.astro` — agregar `<WebMCPRegistration apiBase={...} niche="<app>" />`
  - Verificar: build exitoso + script inline visible en `dist/index.html`

### shared (libreria comun del backend)

- `serverless/lambda/shared/lambda_kit/http_dispatch.py` — agregar soporte para POST con JSON body (si no lo tiene ya tras el plan c-cv-data-service)
  - Verificar: `python devtools/run.py serverless tests --type=unit --lambda=cv` sigue verde (no rompe el comportamiento existente)
  - Verificar: nuevo test del nlweb para POST pasa

### devtools (un solo archivo)

- `devtools/pyproject.toml` — agregar `beautifulsoup4` a `[dependency-groups]` dev
  - Verificar: `cd devtools && uv sync --frozen`
  - Verificar: `uv run python -c "import bs4; print(bs4.__version__)"` imprime version

## Eliminar

- `docs/specs/ai-readiness-2026/` (la carpeta entera) — en el ULTIMO commit del PR
  - Verificar: `git status` no muestra `docs/specs/ai-readiness-2026/` tras el commit final
  - Razon: la carpeta es efimera (ver `.claude/rules/plan-format.md`)

## Resumen por dominio

| Dominio | Crear | Modificar | Total |
|---------|-------|-----------|-------|
| `packages/seo/` | 8 archivos | 1 | 9 |
| `packages/app-shared/` | ~5 archivos | 2 | 7 |
| `apps/<app>/` (x6) | 4 archivos x 6 = 24 | 3 x 6 = 18 | 42 |
| `serverless/lambda/services/nlweb/` | ~20 archivos | 0 | 20 |
| `serverless/lambda/shared/` | 0 | 1 | 1 |
| `devtools/` | 9 archivos | 1 | 10 |
| `tests/feature/` | 3 archivos | 0 | 3 |
| **Total** | **~69** | **~23** | **~92** |
