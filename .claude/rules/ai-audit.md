# AI readiness audit (devtools `ai_audit`)

> Como auditar que tan preparado esta el portfolio para crawlers/agentes
> de IA (ClaudeBot, GPTBot, PerplexityBot) usando el script
> `devtools/ai_audit`. Combina 3 fuentes complementarias 100% gratis:
> isitagentready (Cloudflare API JSON), validators OSS propios y
> Google PageSpeed Insights (API key gratis). Produce snapshot JSON +
> reporte Markdown comparativo.

## Activacion

Aplica SIEMPRE que se trabaje con:

- El script `python devtools/run.py ai_audit [...]`
- Cualquier archivo bajo `devtools/ai_audit/`
- `PSI_API_KEY` en `docker/env/dev-cli/.{env}` (Google PageSpeed Insights)
- Reportes generados en `tmp/ai-audit/<timestamp>/`
- Decisiones de "que mejorar primero para GEO/AI SEO" basadas en
  estos scores

NO aplica al SEO tradicional (Google Search Console, Lighthouse SEO
en CI). Tampoco a estrategia general de portfolio (skill
`modern-portfolios`).

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** correr el audit contra **prod** como fuente de verdad.
  dev tiene `noindex` + robots bloqueando AI crawlers por
  diseno; auditarlo da scores falsos negativos. El flag `--env=dev`
  existe solo para validar regresiones de config (ej. confirmar que
  dev SI bloquea bots).
- **SIEMPRE** la `PSI_API_KEY` (lighthouse_psi) vive en
  `docker/env/dev-cli/.{env}` — categoria `dev-cli`, LOCAL-ONLY,
  gitignored. NUNCA en `client/`, `server/` ni en SSM.
- **SIEMPRE** los reportes van a `tmp/ai-audit/<timestamp>/` — NUNCA
  a `docs/` ni a la raiz del repo. `tmp/` esta gitignored.
- **SIEMPRE** el orden de prioridad de fixes es: severity DESC, luego
  reach DESC (cuantos crawlers se ven afectados). El reporte lo
  ordena solo.
- **SIEMPRE** las 3 tools son INDEPENDIENTES — un fallo en una
  NUNCA aborta el run global; se reporta como `BLOCKED`, `ERROR` o
  `SKIPPED` y se continua. Hard guard en `scraper.run_audit`.
- **SIEMPRE** retry con backoff exponencial (5s, 15s, 45s) ante 4xx,
  5xx, timeout. Tras 3 intentos: skip + reportar.
- **SIEMPRE** la `PSI_API_KEY` se extrae con
  `grep -m1 '^PSI_API_KEY='` del archivo del env activo (NUNCA cargar
  el `.env` completo — ver [env-files.md](env-files.md)).
- **NUNCA** correr el audit en CI/CD automatico — es consumo de APIs
  externas (PSI: 25k/dia free, isitagentready: sin rate-limit oficial
  pero ToS implicito). Solo manual on-demand.
- **NUNCA** commitear `tmp/ai-audit/` (esta gitignored).
- **NUNCA** commitear el `.env` con la `PSI_API_KEY` (gitignored por
  categoria dev-cli).

## Tools activas (3)

| Tool | Tipo | Auth | Score range |
|---|---|---|---|
| `isitagentready` | API JSON publica de Cloudflare | Anonima | 0-5 (level) |
| `validators` | Codigo OSS propio (httpx + bs4) | Anonima | 0-100 (% checks pass) |
| `lighthouse_psi` | Google PageSpeed Insights v5 API | API key gratis | 0-100 (avg de 4 cats Lighthouse) |

### isitagentready (Cloudflare)

`POST https://isitagentready.com/api/scan` con `{url: target}`. Devuelve
checks por categoria (`pass`/`fail`/`neutral`) + `nextLevel.requirements`
para subir de nivel. El score 0-5 corresponde a los niveles:
0 No-Bot-Aware → 5 Agent-Native.

### validators (codigo OSS propio)

Fetchea 4 recursos del target en paralelo y los pasa por validadores
puros en `ai_audit/validators.py`:

1. `/llms.txt` segun spec llmstxt.org (H1 + links + size < 100 KB)
2. `/robots.txt` para AI bots conocidos (GPTBot, ClaudeBot,
   PerplexityBot, CCBot, Google-Extended, etc.). Detecta `Disallow: /`
   bloqueando bots accidentalmente.
3. `/sitemap.xml` shape valida + count de URLs.
4. JSON-LD `Person` u `Organization` en el HTML del home.

Score = % de los 4 checks con status `pass`.

### lighthouse_psi (Google PageSpeed Insights)

`GET https://www.googleapis.com/pagespeedonline/v5/runPagespeed` con
`?url=<X>&key=<K>&category=PERFORMANCE&category=SEO&...`. Devuelve los
4 scores Lighthouse (0-100 c/u) + audits failing con su weight.

Si no hay `PSI_API_KEY` en `docker/env/dev-cli/.{env}`: devuelve
`SKIPPED` con un mensaje que linkea a Google Cloud Console.

## Comando canonico

```bash
# Default: 6 homes de prod, las 3 tools
python devtools/run.py ai_audit

# Subset de niches (solo homes)
python devtools/run.py ai_audit --niches=hub,fintech

# Custom targets (niche + path)
python devtools/run.py ai_audit \
  --targets=architect:/projects,leader:/about

# Subset de tools (skip lighthouse si no tienes key todavia)
python devtools/run.py ai_audit \
  --tools=isitagentready,validators

# Re-render del Markdown desde un snapshot JSON existente
python devtools/run.py ai_audit report \
  --snapshot=tmp/ai-audit/2026-05-25T10-30-00/snapshot.json
```

Status por (target, tool): `OK` (score capturado) / `PARTIAL` (parcial)
/ `BLOCKED` (HTTP 4xx/5xx tras 3 retries) / `ERROR` (excepcion no
recuperable) / `SKIPPED` (config faltante, ej. PSI_API_KEY).

## Flujo de trabajo

1. **Antes de correr el audit**: confirmar que prod esta deployado y
   accesible publicamente.
2. **Primera vez**: obtener API key de Google PageSpeed Insights y
   pegarla en `docker/env/dev-cli/.<env>` con la key
   `PSI_API_KEY=<tu_key>` (ver "Setup PSI key" abajo).
3. **Run**: el comando ejecuta hasta 18 audits (6 URLs x 3 tools por
   env) en ~30-60s.
4. **Lectura del reporte**: abrir `report.md` del run. Top 5 fixes
   priorizados con `severity` + `reach`.
5. **Iteracion**: aplicar fixes, redeployar prod, re-correr.

## Setup `PSI_API_KEY` (Google PageSpeed Insights)

Una sola vez por dev. La key es **gratis** (sin tarjeta), 25 000
requests/dia es mas que suficiente.

1. https://console.cloud.google.com/apis/credentials
2. Crear/usar un proyecto.
3. Habilitar "PageSpeed Insights API" (busca en la library de APIs).
4. Create Credentials → API key. Copiar la key.
5. Restringir la key a "PageSpeed Insights API" (defensa en
   profundidad).
6. Pegar en `docker/env/dev-cli/.local` (y los otros envs si quieres
   separar) con el formato `PSI_API_KEY=<tu_key>` (sin comillas, sin
   espacios alrededor del `=`).
7. El tool la lee en runtime con
   `grep -m1 '^PSI_API_KEY=' docker/env/dev-cli/.<env>`. NUNCA carga
   el `.env` completo (cumple `env-files.md`).

Si no esta seteada, `lighthouse_psi` reporta `SKIPPED` y el run
continua con isitagentready + validators.

## Tools descartadas (mayo 2026) — no reabrir

| Tool | Razon |
|---|---|
| aibotchecker.online | No tiene API JSON publica; "free check" requiere signup; overlap 99% con isitagentready |
| Ahrefs AI Visibility | API key cuesta $500+/mes (Brand Radar); free webapp sin endpoint JSON; reverse-engineering = riesgo ToS |
| Semrush AI Visibility | API requiere plan Business $499/mes + addon $99/mes; free tier sin acceso a API |
| Cloro (cloro.dev) | Plan minimo $100/mes (250k credits); el research previo lo presento como free 500 credits — falso, returns HTTP 401 sin API key |
| HubSpot AEO Grader | Brand-based (no URL-based), pide `companyName`+`geography`+`industry`; reCAPTCHA en form |

Detalle de cada descarte: [.claude/docs/ai-audit/01-tools-evaluadas.md](../docs/ai-audit/01-tools-evaluadas.md).

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Correr el audit cada commit en CI | Consumo de APIs externas + ToS riesgo | Manual on-demand, max 1-2 por semana |
| Auditar dev como gate de PR | Ese env bloquea AI crawlers por diseno | Solo prod como gate |
| Commitear `tmp/ai-audit/` al repo | Es scratch; pollute history | Esta en `.gitignore` |
| Hardcodear `PSI_API_KEY` en codigo o yaml | Secreto leak en git | Solo en `docker/env/dev-cli/.{env}` |
| Confiar solo en isitagentready | No mide performance ni JSON-LD del HTML rendered | Combinar las 3 tools (isitagentready + validators + lighthouse_psi) |
| Bloquear el run global si un tool falla | Las 3 son ortogonales | scraper.py tiene hard guard que continua con la siguiente |
| Implementar tracker de score historico en JSONL | Scope creep — el MVP es snapshot puntual | Diferir si hay demanda |
| Scrapear paths internos sin override explicito | PSI cobra quota por request; gastar en `/404` es desperdicio | Default = home; paths internos via `--targets=` |
| Re-anadir aibotchecker/Ahrefs/Semrush sin discutir | Ya descartados con razones documentadas | Si crees que reapareciera valor, abrir issue antes de PR |

## Ceiling intencional del score isitagentready

El portfolio NO implementa estos checks por decision arquitectonica:

- `/.well-known/openid-configuration` — el portfolio NO tiene auth real.
  Publicar un stub OAuth/OIDC es anti-pattern y confunde a los agentes
  (intentaran iniciar un flujo OAuth que no existe). Joost.blog (83/100
  = Level 5) deliberadamente rechaza este check por la misma razon.
- `/.well-known/oauth-protected-resource` — idem. Turnstile CAPTCHA del
  Lambda de contacto NO es OAuth standard.

**Ceiling esperado**: isitagentready 3-4/5. Aceptar la penalizacion
intencional de esos 2 checks es correcto. Cualquier "fix" que publique
stubs de auth se debe rechazar en code review.

## MCP server endpoint (Pages Functions, Free tier)

Los 6 niches del portfolio exponen un MCP server (Model Context Protocol
2025-11-25, JSON-RPC 2.0 sobre HTTP) en `/mcp`:

- **Codigo compartido**: paquete `@portfolio/mcp` con handlers
  `initialize`, `tools/list`, `tools/call`.
- **3 tools fijas**: `get_cv_section(section)`, `list_projects(tech_stack?)`,
  `search_experience(keyword)`. NO se agregan tools nuevas sin
  justificacion + actualizar el server card builder.
- **Bundling**: `apps/<niche>/scripts/postbuild-functions.mjs` bundlea
  `apps/<niche>/functions/mcp.ts` a `apps/<niche>/dist/functions/mcp.js`
  via esbuild (Workers-compatible ESM). Wrangler recoge `dist/functions/`
  al hacer `pages deploy dist`.
- **Server card publico**: `/.well-known/mcp/server-card.json` generado
  por prebuild via `packages/seo/src/lib/build-mcp-server-card.ts`
  (importa los 3 tools de `@portfolio/mcp` para evitar duplicacion).

**SIEMPRE** ANTES de extender el MCP server con tools nuevas, leer la
decision de scope arriba. Cualquier tool nueva implica: (1) modulo en
`packages/mcp/src/lib/tools/`, (2) registro en
`packages/mcp/src/lib/tools/index.ts`, (3) tests con BDD-style,
(4) verificar que el server card se regenera correcto en build local.

## Bug Cloudflare Pages: rutas sin extension caen en SPA fallback

Documentado en `docs/specs/ai-audit-level-3-4/02-fase-0-diagnostico.md`:
Cloudflare Pages devuelve el `index.html` (~83 KB) para cualquier ruta
sin extension reconocida, aunque el archivo real exista en el bucket.

**Workaround estandar**: publicar el archivo con extension (`.json`,
`.xml`, `.txt`) + agregar rewrite `200` en `_redirects` para mantener
la URL canonica sirviendo el mismo body:

```text
/.well-known/api-catalog /.well-known/api-catalog.json 200
```

Si en el futuro se agrega otro `.well-known/<X>` sin extension, aplicar
el mismo patron.

## Referencias cruzadas

- Skill: [`/ai-audit`](../skills/ai-audit/SKILL.md) — invocacion
  manual con keywords ES/EN
- Docs (knowledge tree): [.claude/docs/ai-audit/](../docs/ai-audit/)
  — tools evaluadas, setup PSI key, arquitectura, troubleshooting
- Skill relacionada: [`/modern-portfolios`](../skills/modern-portfolios/SKILL.md)
  — GEO + ATS + estrategia general; el audit es la medicion de eso
- Skill relacionada: [`/ai-prompt-optimization`](../skills/ai-prompt-optimization/SKILL.md)
  — white-hat AI SEO (JSON-LD, llms.txt, robots.txt) que el audit valida
- Rule relacionada: [secrets-strategy.md](secrets-strategy.md) —
  donde vive la `PSI_API_KEY` (categoria `dev-cli`)
- Rule relacionada: [env-files.md](env-files.md) — NUNCA leer `.env`
  completos; extraer keys puntuales
- Rule relacionada: [devtools.md](devtools.md) — convenciones de
  scripts en `devtools/`
- Rule relacionada: [python.md](python.md) — Python 3.14, ruff, testing
