# 01 - Tools evaluadas

> Detalle de cada una de las 4 tools que el script `ai_audit` scrapea.
> Una seccion por tool: URL, auth, datos capturados, gotchas del DOM,
> frecuencia esperada de breakage.

[< README](README.md) | [02 Auth setup >](02-auth-setup.md)

## 1. Is Your Site Agent-Ready? (isitagentready)

| Campo | Valor |
|-------|-------|
| URL del audit | `https://isitagentready.com` |
| Auth | Anonima |
| Respaldo | Cloudflare (oficial, lanzada abril 2026) |
| Disclaimer en pie | "AI-generated recommendations. AI can make mistakes... Cloudflare assumes no liability" |
| Que devuelve | Score global 0-100 + 5 categorias: Discoverability, Content Accessibility, Bot Access Control, Protocol Discovery, Commerce Standards |
| Detalle por categoria | Lista de checks pasados/fallados con recomendacion copy-paste para coding agents (Claude Code, Cursor) |
| Rate-limit observado | ~1 audit cada 10s por IP. Si dispara captcha, retry con backoff suele resolver |
| DOM stable | Selectores conviven con clases hash; preferir matching por data-attributes o aria-labels |

**Parser captura**:

- `score` global (numero)
- `categories` dict {nombre: score}
- `fixes` lista de hasta 5 con `{severity, category, issue, fix, file?}`

## 2. AI Visibility Checker (aibotchecker)

| Campo | Valor |
|-------|-------|
| URL del audit | `https://aibotchecker.online` |
| Auth | Anonima |
| Respaldo | Independiente (no afiliada a Cloudflare ni a SEO suites) |
| Que devuelve | 60+ checks per-agent con severidad. Compara crawl con user-agent de browser vs user-agent de cada AI bot (GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot, ChatGPT-User, Anthropic-Claude-Web, Google-Extended, CCBot) |
| Detalle por agente | Status (allow/block) + accesibilidad efectiva + diffs HTML vs browser |
| Rate-limit observado | Mas tolerante (~1 audit cada 5s). Pero respeta robots.txt — si bloqueas su crawler en robots.txt, no funciona |
| DOM stable | Tabla per-agent estable. Severidad por color (clase CSS) |

**Parser captura**:

- `score` global (numero) si lo expone; si no, agregado ponderado por agente
- `categories` dict {agente: status_summary}
- `fixes` lista de hasta 5 ordenadas por severidad

## 3. Ahrefs AI Visibility Checker

| Campo | Valor |
|-------|-------|
| URL del audit | `https://ahrefs.com/ai-visibility-checker` |
| Auth | Cuenta Ahrefs gratis (Ahrefs Webmaster Tools) |
| Respaldo | Ahrefs (proveedor SEO) |
| Que devuelve | Brand mentions y citaciones en respuestas de ChatGPT, Gemini, Perplexity, Microsoft Copilot, Google AI Overviews |
| Detalle | Lista de prompts donde aparece el dominio + sentiment + posicion |
| Rate-limit observado | Estricto (~5 checks/dia cuenta free) |
| DOM stable | Cambia frecuentemente — UI suite. Selectores via data-test-id donde existan |

**Parser captura**:

- `score` global = nro de plataformas IA donde aparece (0-5)
- `categories` dict {plataforma: nro_mentions}
- `fixes` lista con sugerencias del propio Ahrefs (si las muestra) o vacia

**StorageState**: `docker/env/dev-cli/ai-audit/ahrefs.json` (LOCAL-ONLY).

## 4. Semrush AI Visibility Audit

| Campo | Valor |
|-------|-------|
| URL del audit | `https://www.semrush.com/ai-visibility-audit` |
| Auth | Cuenta Semrush gratis |
| Respaldo | Semrush (proveedor SEO) |
| Que devuelve | AI readiness score + technical blocking + content audit + trafico real desde plataformas IA |
| Detalle | Lista de issues tecnicos + sugerencias + integracion con sitemap y robots.txt del usuario |
| Rate-limit observado | Estricto en cuenta free; ~2-3 audits/dia para dominios nuevos |
| DOM stable | Cambia con releases del producto. Suite SaaS — sin contrato de estabilidad |

**Parser captura**:

- `score` global 0-100
- `categories` dict {Technical, Content, Visibility}
- `fixes` lista de hasta 5 con severidad

**StorageState**: `docker/env/dev-cli/ai-audit/semrush.json` (LOCAL-ONLY).

## Ranking de fragilidad

| Tool | Fragilidad del scraper | Razon |
|------|------------------------|-------|
| isitagentready | Baja | UI simple, dominio estable, sin login |
| aibotchecker | Baja | UI tabular estable, sin login |
| Ahrefs | Alta | Suite SaaS que cambia DOM con releases + auth |
| Semrush | Alta | Idem Ahrefs, ademas dashboard mas dinamico |

Si Ahrefs o Semrush rompen el parser, el script reporta `ERROR` para
ese (target, tool) y continua. El reporte final lo lista para que el
dev decida si actualizar el selector ahora o despues.

## Por que estas 4 y no otras

| Alternativa | Por que NO incluirla |
|-------------|----------------------|
| Profound (profound.com) | API de pago, no scraping practico |
| Otterly (otterly.ai) | Solo paid, dataset cerrado |
| Brandwise / AI Brand Search | Mercado nuevo, sin trayectoria de estabilidad de DOM |
| Lighthouse / PageSpeed Insights | Mide perf/SEO clasico, NO agent-readiness |

Si en el futuro alguna 5ta vale la pena, agregar un nuevo archivo
en `devtools/ai_audit/tools/<nombre>.py` siguiendo el contrato.

[< README](README.md) | [02 Auth setup >](02-auth-setup.md)
