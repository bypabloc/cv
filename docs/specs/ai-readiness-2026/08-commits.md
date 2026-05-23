# 08 — Commits (secuencia atomica)

> Listado de commits que implementan el plan. Cada commit deja el repo
> verde (lint + typecheck + tests del scope) y referencia los AC que
> cubre. Conventional Commits en espanol.

## Rama y PR

- Branch: `feature/ai-readiness-2026` desde `dev`
- PR: 1 solo, `feature/ai-readiness-2026 -> dev`. Promocion a stage y
  main por separado (ver `.claude/rules/git-workflow.md`).

## Secuencia de commits

### Base secuencial (commits 1-3) — NO se paralelizan

#### Commit 1 — Crear la carpeta del plan

```text
docs(specs): plan ai-readiness-2026 para subir Cloudflare Agent Readiness Score a 70+

- Agrega docs/specs/ai-readiness-2026/ con README + 10 archivos de plan
- Estado actual del portfolio (scan 22-May-2026): 33/100, falla 6 items en API/MCP
- Objetivo: 70+ via 5 fases (well-known endpoints, content negotiation, NLWeb Lambda, WebMCP runtime, script de scan)
- Decisiones cerradas: 6 apps cada una expone .well-known; Lambda nlweb nueva separada; sin LLM (retrieval estructurado); scan via Playwright scraping
```

- Archivos: solo `docs/specs/ai-readiness-2026/**`
- Cubre AC: ninguno (es el plan)
- Verificacion: `git status` muestra carpeta nueva; no rompe nada

#### Commit 2 — Data layer compartido en `@portfolio/seo`

```text
feat(seo): agrega data compartida para AI-readiness (MCP_TOOLS, resolveApiBase)

- packages/seo/src/data/mcp-tools.ts: 4 tools tipadas (cv.get_experiences, cv.get_projects, cv.get_skills, nlweb.ask) con Zod schema
- packages/seo/src/data/api-base.ts: resolveApiBase(siteUrl) resuelve api.portfolio.{dev,stage,prod} segun host
- Tests unit con 100% coverage en data/
- Exports nuevos en packages/seo/src/index.ts: MCP_TOOLS, McpToolSchema, McpTool, resolveApiBase
```

- Archivos: `packages/seo/src/data/{mcp-tools,api-base}.ts`,
  `packages/seo/src/index.ts`, tests mirror
- Cubre AC: prep para AC-1/AC-2 (sin endpoints aun)
- Verificacion: `python devtools/run.py test_runner --module=pkg-seo --type=coverage`

#### Commit 3 — `http_dispatch` soporta POST con body JSON (en shared.lambda_kit)

```text
feat(shared): http_dispatch soporta POST con body JSON

- shared/lambda_kit/http_dispatch.py: extract_request_post() parsea body JSON valido
- Tests unit: test_extract_request_post_returns_operation_action_data, test_extract_request_post_invalid_json_raises
- Mantiene compatibilidad con GET (Lambda cv sigue verde)
```

- Archivos: `serverless/lambda/shared/lambda_kit/http_dispatch.py`,
  tests unit nuevos
- Cubre AC: prep para AC-8
- Verificacion: `python devtools/run.py serverless tests --type=unit --lambda=cv` sigue verde

> Si el plan `c-cv-data-service` (ya mergeado) dejo el soporte POST,
> este commit se SKIPEA y se actualiza `08-commits.md` y los numeros se
> compactan.

### Fase 1 (commits 4-9) — well-known endpoints

#### Commit 4 — Builders del `@portfolio/seo`

```text
feat(seo): agrega builders buildApiCatalog, buildMcpServerCard, buildAgentSkills

- 3 builders nuevos en packages/seo/src/lib/
- Conformes a RFC 9727 (linkset), SEP-2127 (MCP Server Card), agentskills.io 0.2.0
- Cada builder es funcion pura, recibe { siteUrl, niche? } y retorna objeto serializable
- Tests unit AAA + BDD-style >= 80% coverage per-file
```

- Archivos: 3 builders + 3 tests + actualizar `index.ts`
- Cubre AC-1, AC-2, AC-3 (logica, sin endpoints todavia)
- Verificacion: `python devtools/run.py test_runner --module=pkg-seo --type=coverage`

#### Commit 5-9 — Endpoints en las 6 apps (1 commit por app)

> ALTERNATIVA: 1 solo commit "feat(apps): expone .well-known endpoints
> en las 6 apps" que toca las 6 apps juntas. Decision: **un commit por
> app** porque cada uno se puede revertir aislado si hay regresion.

Patron del mensaje (repetido x6):

```text
feat(<app>): expone .well-known/{api-catalog, mcp/server-card.json, agent-skills/index.json}

- 3 endpoints Astro en apps/<app>/src/pages/.well-known/
- Usan los builders de @portfolio/seo con niche='<app>'
- Headers Content-Type correctos (application/linkset+json para api-catalog)
- Cache-Control: public, max-age=3600
```

- Archivos: 3 por app
- Cubre AC: AC-1, AC-2, AC-3, AC-4 (al completar las 6 apps)
- Verificacion: `pnpm --filter @portfolio/<app> run build` + `ls
  apps/<app>/dist/.well-known/*` muestra los 3 archivos

### Fase 2 (commits 10-11) — Content negotiation + Link headers

#### Commit 10 — Middleware compartido en `@portfolio/app-shared`

```text
feat(app-shared): middleware ai-content para markdown negotiation + Link headers

- packages/app-shared/src/middleware/ai-content.ts: detecta Accept: text/markdown
  y devuelve markdown via turndown; agrega Link header con rel api-catalog/mcp/agent-skills/service-doc en la homepage
- devdep: turndown + @types/turndown
- Tests unit con happy-dom (4 escenarios: markdown, html, link header en /, no link en /about)
```

- Archivos: middleware + tests + `package.json` + `index.ts`
- Cubre AC-5, AC-6, AC-7 (logica)
- Verificacion: `python devtools/run.py test_runner --module=pkg-app-shared --type=coverage`

#### Commit 11 — Wire-up del middleware + adapter Cloudflare en las 6 apps

```text
feat(apps): adopta @astrojs/cloudflare adapter y middleware ai-content en las 6 apps

- astro.config.ts de cada app: adapter cloudflare con mode='directory'
- src/middleware.ts en cada app: re-export del middleware compartido
- devdep @astrojs/cloudflare en cada package.json de app
- Build sigue generando dist/index.html (validado en VERIFICATION del commit)
```

- Archivos: 6 `astro.config.ts` + 6 `middleware.ts` + 6 `package.json`
  = 18 cambios
- Cubre AC-5, AC-6, AC-7 (wire-up)
- Verificacion (CRITICA): cada app, `pnpm --filter <app> run build`
  termina con `dist/index.html` existente. Si no, REVERTIR este commit.

### Fase 3 (commits 12-17) — NLWeb Lambda

#### Commit 12 — Scaffolding del Lambda nlweb

```text
feat(lambda/nlweb): scaffolding inicial del Lambda nlweb

- serverless/lambda/services/nlweb/ siguiendo patron lambda-controller
- manifest.yaml: POST /nlweb/ask, usa cache table + neon-url secret
- pyproject.toml con dependency-groups dev y [tool.shared] internal-deps
- core/{handler.py, controllers/, services/, models/, settings/} bootstrap minimo
- .gitignore excluye build/ y build.zip
- events/ask.json + events/ask_empty.json
```

- Archivos: ~10 archivos en `services/nlweb/` (sin tests aun)
- Cubre AC: prep para AC-8/AC-9/AC-10
- Verificacion: `cd serverless/lambda/services/nlweb && uv sync --frozen && uv run python -m compileall -q core`
- Verificacion: `python devtools/run.py serverless lint-deps --lambda=nlweb` verde

#### Commit 13 — Modelos Pydantic (AskPayload, schema.org)

```text
feat(lambda/nlweb): agrega modelos Pydantic AskPayload y SchemaOrgItemList

- core/models/ask.py: AskPayload con query (1-500 chars), niche optional, limit (1-50)
- core/models/schema_org.py: SchemaOrgItemList, SchemaOrgListItem, SchemaOrgPerson
- Tests unit: un test por validation case (5 archivos)
```

- Archivos: 2 modelos + 5 tests
- Cubre AC: prep
- Verificacion: `python devtools/run.py serverless tests --type=unit --lambda=nlweb`

#### Commit 14 — retrieval_service

```text
feat(lambda/nlweb): retrieval estructurado sobre Neon (sin LLM)

- core/services/retrieval_service.py: tokenize() + retrieve() con ILIKE + ranking por overlap
- Soporta filtro por niche via join cv_<X>_niches
- Consulta cv_experiences, cv_projects, cv_skills
- Tests unit: 3 archivos (filters_by_niche, ranks_by_overlap, returns_empty)
```

- Archivos: 1 service + 3 tests
- Cubre AC-9 (empty case)
- Verificacion: tests verdes

#### Commit 15 — schema_org_service + controller Ask

```text
feat(lambda/nlweb): schema_org_service y Ask controller con @cached

- core/services/schema_org_service.py: to_schema_org() wrap en ItemList con @context schema.org
- core/controllers/nlweb/ask.py: Ask(BaseController) con preload/validate/execute
- Cache: @cached(ttl=300, key_prefix='nlweb:ask') hereda de shared.cache
- Tests unit: 4 archivos (wraps_in_itemlist, emits_person_context, controller_*)
```

- Archivos: 1 service + 1 controller + 4 tests
- Cubre AC-8, AC-10
- Verificacion: tests + coverage >= 80%

#### Commit 16 — Handler + handler tests

```text
feat(lambda/nlweb): handler.py expone POST /nlweb/ask con Content-Type ld+json

- core/handler.py: lambda_handler() invoca http_dispatch.http_handler con OPERATIONS
- Response Content-Type: application/ld+json (override del default text/plain)
- Headers X-Cache: HIT/MISS visibles para verificacion del cache
- Tests unit: 4 archivos (ask_action_200, missing_query_400, cache_hit_header, empty_returns_0)
```

- Archivos: 1 handler + 4 tests
- Cubre AC-8, AC-9, AC-10
- Verificacion: `python devtools/run.py serverless tests --type=coverage --lambda=nlweb` >= 80%

#### Commit 17 — Tests integration + deploy a dev

```text
feat(lambda/nlweb): tests integration contra Neon dev y deploy a dev

- tests/integration/test_ask_e2e_fintech_query_returns_real_data.py
- tests/integration/_fixtures/seeded_cv.py asegura datos antes del test
- Deploy a dev y smoke test con curl:
    curl -X POST 'https://api.portfolio.dev.the-full-stack.com/nlweb/ask' \
      -H 'Content-Type: application/json' \
      -d '{"query": "fintech"}' \
      → 200 con itemListElement no vacio
```

- Archivos: tests integration nuevos
- Cubre AC-8 (validacion E2E)
- Verificacion: `python devtools/run.py serverless tests --type=integration --lambda=nlweb`
- Verificacion: `serverless deploy --lambda=nlweb --stage=dev`
- Verificacion: curl smoke test pasa

### Fase 4 (commits 18-19) — WebMCP runtime

#### Commit 18 — Componente compartido WebMCPRegistration

```text
feat(app-shared): componente WebMCPRegistration registra tools en navigator.modelContext

- packages/app-shared/src/components/WebMCPRegistration.astro: script inline con feature-detect
- Las tools son las mismas de MCP_TOOLS (lectura unica desde @portfolio/seo)
- Tests unit: 2 escenarios (script presente con tools, no rompe sin navigator.modelContext)
```

- Archivos: 1 componente + 2 tests + actualizar `index.ts`
- Cubre AC-11, AC-12 (logica)
- Verificacion: `python devtools/run.py test_runner --module=pkg-app-shared --type=coverage`

#### Commit 19 — Wire-up en BaseLayout de las 6 apps

```text
feat(apps): incluye WebMCPRegistration en BaseLayout de las 6 apps

- apps/<app>/src/layouts/BaseLayout.astro: importa WebMCPRegistration y resolveApiBase
- Pasa { apiBase, niche='<app>' } como props
- 6 archivos modificados, mismo cambio
```

- Archivos: 6 `BaseLayout.astro`
- Cubre AC-11
- Verificacion: build de las 6 apps + script visible en `dist/index.html`

### Fase 5 (commit 20) — Script de scan

#### Commit 20 — devtools agent_readiness_scan

```text
feat(devtools): script agent_readiness_scan via Playwright scrapping

- devtools/agent_readiness_scan/ con main.py, flags.py, scanner.py, parser.py, reporter.py
- Soporta --url repetible, --min-score como gate, --output JSON
- Tests unit del parser (fixture HTML del scanner del 22-May-2026)
- Devdep beautifulsoup4 agregada al devtools/pyproject.toml
```

- Archivos: paquete completo en `devtools/agent_readiness_scan/` + tests + `pyproject.toml`
- Cubre AC-13 (la herramienta para medir)
- Verificacion: `python devtools/run.py test_runner --module=devtools --type=unit`
- Verificacion: smoke test `python devtools/run.py agent_readiness_scan --url=https://the-full-stack.com` retorna JSON

### Fase 6 (commit 21) — Verificacion E2E + cleanup del plan

#### Commit 21 — chore(specs): elimina plan ai-readiness-2026 tras verificacion E2E completa

```text
chore(specs): elimina docs/specs/ai-readiness-2026/ tras verificacion E2E completa

- Verificacion E2E iterativa (Parte A): refactor de tests OK (no quedan refs a archivos eliminados)
- Verificacion E2E iterativa (Parte B): bateria completa en verde
  * Lint + typecheck + unit + build (las 6 apps) ✓
  * Tests unit y coverage de packages/seo, packages/app-shared >= 80% ✓
  * Tests del Lambda nlweb (unit + integration + coverage >= 80%) ✓
  * Tests E2E Playwright en las 6 apps (well-known, content-negotiation, webmcp) ✓
- Scan stage post-deploy:
  * https://stage.the-full-stack.com → 75/100 (Level 4 Agent-Ready) ✓
  * Los 6 subdominios reportan score >= 70 ✓
- Resumen en docs/progress/agent_readiness_stage_<ts>.json
- Plan ya implementado: la carpeta es efimera (rule plan-format)
```

- Archivos: `git rm -r docs/specs/ai-readiness-2026/`
- Cubre AC-13, AC-14 (verificacion del score real)
- Verificacion: la bateria de la fase 6 completa pasa
- Si la bateria NO pasa: NO se commitea esto. Iterar, fix, re-ejecutar.

## Resumen

| # | Commit | Fase | Archivos | Verificacion |
|---|--------|------|----------|--------------|
| 1 | docs(specs): plan ai-readiness-2026 | 0 | plan | git status |
| 2 | feat(seo): data compartida | 0 | data/ + tests | coverage pkg-seo |
| 3 | feat(shared): http_dispatch POST | 0 | shared/lambda_kit | unit tests cv |
| 4 | feat(seo): 3 builders | 1 | lib/ + tests | coverage pkg-seo |
| 5-9 | feat(<app>): well-known endpoints | 1 | apps x6 (3 archivos c/u) | build x6 |
| 10 | feat(app-shared): middleware ai-content | 2 | middleware + tests | coverage pkg-app-shared |
| 11 | feat(apps): adapter cloudflare + middleware | 2 | apps x6 | build x6 (dist/index.html) |
| 12 | feat(lambda/nlweb): scaffolding | 3 | services/nlweb/ | uv sync + compileall |
| 13 | feat(lambda/nlweb): modelos | 3 | models + tests | unit tests nlweb |
| 14 | feat(lambda/nlweb): retrieval_service | 3 | service + tests | unit tests nlweb |
| 15 | feat(lambda/nlweb): schema_org + Ask | 3 | service + controller + tests | coverage nlweb >= 80% |
| 16 | feat(lambda/nlweb): handler | 3 | handler + tests | coverage nlweb >= 80% |
| 17 | feat(lambda/nlweb): integration + deploy | 3 | integration tests | deploy dev + curl |
| 18 | feat(app-shared): WebMCPRegistration | 4 | componente + tests | coverage pkg-app-shared |
| 19 | feat(apps): WebMCPRegistration en BaseLayout | 4 | apps x6 | build x6 + script visible |
| 20 | feat(devtools): agent_readiness_scan | 5 | devtools/agent_readiness_scan/ | unit tests devtools + smoke |
| 21 | chore(specs): elimina ai-readiness-2026 | 6 | rm -r docs/specs/... | bateria E2E completa verde |

**Total: 21 commits**.
