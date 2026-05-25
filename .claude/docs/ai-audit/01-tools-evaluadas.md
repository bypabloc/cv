# 01 - Tools evaluadas

> Detalle de las 3 tools activas + las 5 descartadas. El stack actual
> son las 3 que ofrecen acceso libre real (API publica o codigo OSS
> propio); las otras 5 fueron descartadas tras verificacion directa.

[< README](README.md) | [02 Auth setup >](02-auth-setup.md)

## Tools activas (3)

### 1. isitagentready (Cloudflare)

| Campo | Valor |
|-------|-------|
| Endpoint | `POST https://isitagentready.com/api/scan` |
| Auth | Anonima |
| Respaldo | Cloudflare (oficial, lanzada abril 2026) |
| Que devuelve | Level 0-5 (0=No-Bot-Aware, 5=Agent-Native), 5 categorias: discoverability, contentAccessibility, botAccessControl, discovery, commerce. Cada categoria con checks pass/fail/neutral |
| Rate-limit observado | ~1 audit/10s por IP, sin rate-limit oficial documentado |
| Notas | El sitio tiene MCP server en `/.well-known/mcp.json`; el endpoint `/api/scan` es la fuente que la UI consume internamente |

**Parser captura** (en `ai_audit/tools/isitagentready.py`):

- `score` = `level` (0-5)
- `categories` dict con % de checks `pass` por categoria (excluye `neutral` del divisor)
- `fixes` lista de hasta 5 priorizada por `nextLevel.requirements` (HIGH) + checks failing (MEDIUM)

### 2. validators (codigo OSS propio)

| Campo | Valor |
|-------|-------|
| Tipo | Codigo Python (httpx + bs4), sin dep externa pesada |
| Auth | Anonima |
| Que devuelve | 4 checks: llms.txt spec, robots.txt AI bots blocked, sitemap.xml validez, JSON-LD Person/Organization |
| Notas | Fetcha los 4 recursos en paralelo con asyncio.gather; cada validator es una funcion pura testeable sin red |

**Validators** (en `ai_audit/validators.py`):

- `validate_llms_txt(content)` — header H1 + links markdown + size < 100 KB (spec llmstxt.org)
- `validate_robots_ai_bots(content)` — detecta `Disallow: /` en bloques de GPTBot, ClaudeBot, PerplexityBot, CCBot, Google-Extended, ChatGPT-User, OAI-SearchBot, anthropic-ai, Applebot-Extended, cohere-ai
- `validate_sitemap_xml(content)` — shape valida (urlset o sitemapindex) + count de `<loc>`
- `validate_json_ld_person(html)` — extrae todos los `@type` de los `<script type="application/ld+json">` y verifica presencia de `Person` u `Organization`

**Tool wrapper** (en `ai_audit/tools/validators.py`):

- `score` = % de los 4 checks con status `pass`
- `categories` dict con 100 o 0 por cada check
- `fixes` lista con severity HIGH para robots/json-ld (impacto en discoverability), MEDIUM para llms/sitemap

### 3. lighthouse_psi (Google PageSpeed Insights)

| Campo | Valor |
|-------|-------|
| Endpoint | `GET https://www.googleapis.com/pagespeedonline/v5/runPagespeed` |
| Auth | API key gratuita (Google Cloud Console, sin tarjeta) |
| Free tier | 25 000 requests/dia, 100 req/100s |
| Que devuelve | 4 categorias Lighthouse 0-100: Performance, SEO, Accessibility, BestPractices + audits failing con weight |
| Notas | El cold scan demora ~10-30s. Si la key no esta seteada, el tool reporta SKIPPED sin abortar el run |

**Parser captura** (en `ai_audit/tools/lighthouse_psi.py`):

- `score` = promedio de las 4 categorias Lighthouse
- `categories` dict con score 0-100 por categoria (o `'n/a'` si Lighthouse no la corrio)
- `fixes` Top 5 audits failing ordenados por `weight DESC` con severity por threshold (>=5 HIGH, >=2 MEDIUM, sino LOW)

**Setup**: ver [02-auth-setup.md](02-auth-setup.md).

## Tools descartadas (5)

### a. aibotchecker.online — DESCARTADA mayo 2026

| Razon | Detalle |
|-------|---------|
| No tiene API publica | Endpoints comunes (`/api/check`, `/api/scan`, `/api/audit`) responden HTTP 404 |
| Free tier requiere signup | El boton "Run free check" en home no dispara ningun fetch sin login (verificado via XHR sniff) |
| Overlap ~99% con isitagentready | Mide los mismos AI bots (GPTBot, ClaudeBot, PerplexityBot) + robots.txt |

### b. Ahrefs AI Visibility Checker — DESCARTADA mayo 2026

| Razon | Detalle |
|-------|---------|
| API key cuesta $500+/mes | Brand Radar (feature de AI visibility) es addon pago del plan base |
| Webapp gratis sin endpoint JSON | El UI renderea HTML/JS, sin endpoint publico tipo `/api/check` |
| Riesgo legal | Google demando a SerpApi en 2025 por scraping; precedente afecta similares |

### c. Semrush AI Visibility Audit — DESCARTADA mayo 2026

| Razon | Detalle |
|-------|---------|
| API requiere plan Business $499/mes | Free tier no incluye NINGUN acceso a API |
| AI Visibility Toolkit es addon $99/mes adicional | Total minimo ~$600/mes para acceso programatico |
| Webapp gratis con rate-limit estricto | ~2-3 audits/dia para dominios nuevos en cuenta free |

### d. Cloro (cloro.dev) — DESCARTADA mayo 2026

| Razon | Detalle |
|-------|---------|
| Research previo lo presento como "free 500 credits sin signup" | FALSO — verificado directo: `POST /v1/monitor/chatgpt` sin Authorization devuelve HTTP 401 |
| Plan minimo Hobby cuesta $100/mes (250k credits) | Costo por request: 3-7 credits dependiendo del LLM, no escala para auditoria periodica gratis |

### e. HubSpot AEO Grader — DESCARTADA mayo 2026

| Razon | Detalle |
|-------|---------|
| Brand-based, no URL-based | Form pide `companyName`+`geography`+`productsServices`+`industry`, mide presencia de la MARCA en LLMs, no audita una URL |
| reCAPTCHA en el form | `<textarea name="g-recaptcha-response">` bloquea scraping headless |
| No matchea el modelo del portfolio | Un dev sin "brand" empresarial no tiene queries naturales tipo "What does Pablo Contreras sell?" |

## Tools NO evaluadas

| Tool | Razon |
|------|-------|
| Otterly.AI, LLMrefs, SE Ranking | UI-only freemium sin API (verificado en research previo); no scripteables |
| Profound (tryprofound.com) | Requiere signup + plan pago |
| Brave Search API | Free tier eliminado en 2026, ahora metered billing |

Si en el futuro alguna alternativa surge con API publica gratis real,
agregar un nuevo archivo en `devtools/ai_audit/tools/<nombre>.py`
siguiendo el contrato del Protocol `Tool`.

[< README](README.md) | [02 Auth setup >](02-auth-setup.md)
