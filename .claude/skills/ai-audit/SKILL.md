---
name: ai-audit
description: >
  AI readiness audit for the portfolio. Combines 3 free sources via
  devtools/.venv (Python 3.14): isitagentready.com (Cloudflare public
  JSON API), validators OSS (custom — llms.txt + robots.txt AI bots +
  sitemap.xml + JSON-LD Person), and Google PageSpeed Insights API
  (free key, 25k/day). Generates a JSON snapshot + Markdown report
  with top 5 prioritized fixes per niche + env. ALWAYS invoke this
  skill BEFORE answering ANY question about: how AI-ready the
  portfolio is, GEO score, agent-readiness, isitagentready.com,
  llms.txt validation, robots.txt for AI bots, Lighthouse PSI, the
  devtools/ai_audit script, ai_audit catalog of tools, ai_audit
  retry/backoff strategy, where the ai-audit reports live. NEVER
  answer from training data alone — this portfolio has a consolidated
  2026 audit pipeline (3 tools, retry policy, snapshot format) that
  overrides generic advice.
  Use when the user says "ai audit", "ai readiness", "agent ready",
  "agent-readiness", "isitagentready", "is it agent ready", "ai
  visibility", "geo audit", "geo score", "auditar IA", "auditoria IA",
  "auditar para IA", "score de IA", "preparado para IA", "preparado
  para LLM", "preparado para crawlers", "que tan preparado para IA",
  "medir IA seo", "validar llms.txt", "validar robots.txt para AI",
  "lighthouse psi", "pagespeed insights", "ai_audit", "devtools
  ai_audit", "compare niche ai score", "compare niche performance",
  "mcp server portfolio", "mcp endpoint /mcp", "agent-native",
  "level 5 isitagentready", "subir score isitagentready",
  "oauth para portfolio", "openid-configuration portfolio",
  "ceiling ai audit", "que tan agent-ready se puede llegar",
  "que tan agent-capable", "mcp server card", "well-known mcp",
  "model context protocol portfolio".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
argument-hint: "[--env=prod|dev] [--niches=...] [--tools=...] [--targets=niche:/path,...]"
---

# AI readiness audit del portfolio

## Estado (mayo 2026)

Tras eliminar las 3 tools comerciales (aibotchecker, Ahrefs, Semrush)
por costo prohibitivo + falta de API publica, el stack quedo en 3
fuentes complementarias 100% gratis:

| Tool | Tipo | Auth | Que mide |
|------|------|------|----------|
| `isitagentready` | API JSON publica (Cloudflare) | Anonima | 5 categorias: Discoverability, ContentAccessibility, BotAccessControl, Discovery, Commerce (level 0-5) |
| `validators` | Codigo OSS propio (httpx + bs4) | Anonima | 4 checks: llms.txt spec, robots.txt AI bots blocked, sitemap.xml validez, JSON-LD Person/Organization |
| `lighthouse_psi` | Google PageSpeed Insights API v5 | API key gratis | 4 categorias Lighthouse: Performance, SEO, Accessibility, BestPractices |

## Cuando invocar (regla maestra)

Cualquier pregunta sobre "que tan preparada esta esta pagina para IA",
AI/LLM SEO, GEO score, llms.txt/robots.txt para AI bots, performance
scores PSI, o como ejecutar / configurar / interpretar el script
`ai_audit` -> invocar esta skill.

NO invocar para:
- SEO tradicional pre-IA (Google Search Console) -> skill `astro-portfolio`
- Tecnicas white/grey/black-hat de AI SEO -> skill `ai-prompt-optimization`
- Estrategia general del portfolio -> skill `modern-portfolios`

## Comandos canonicos

```bash
# Audit default: 6 homes de prod, las 3 tools
python devtools/run.py ai_audit

# Subset de niches
python devtools/run.py ai_audit --niches=hub,fintech

# Custom targets (niche + path)
python devtools/run.py ai_audit \
  --targets=architect:/projects,leader:/about

# Subset de tools (skip lighthouse si no hay API key)
python devtools/run.py ai_audit \
  --tools=isitagentready,validators

# Re-render del Markdown desde un snapshot JSON existente
python devtools/run.py ai_audit report \
  --snapshot=tmp/ai-audit/2026-05-25T10-30-00/snapshot.json
```

## Output

```text
tmp/ai-audit/<timestamp>/
├── snapshot.json     # crudo: por (target, tool) -> score + categorias + fixes
└── report.md         # tabla comparativa + top fixes priorizados
```

`snapshot.json` shape (resumen):

```jsonc
{
  "ranAt": "2026-05-25T10:30:00Z",
  "env": "prod",
  "targets": ["https://the-full-stack.com", "..."],
  "results": [
    {
      "target": "https://the-full-stack.com",
      "tool": "isitagentready",
      "status": "OK",
      "score": 2,                              // 0-5 (isitagentready) o 0-100
      "categories": {"discoverability": 67, "botAccessControl": 100},
      "fixes": [
        {
          "severity": "high",
          "category": "contentAccessibility",
          "issue": "Support Accept: text/markdown content negotiation",
          "fix": "Enable Markdown for Agents so requests with Accept: text/markdown..."
        }
      ]
    }
  ]
}
```

## API key (solo lighthouse_psi)

Es la unica tool que necesita credencial. La API key es GRATIS de
Google (sin tarjeta), 25 000 req/dia.

**Pasos** (1 vez por dev):
1. https://console.cloud.google.com/apis/credentials
2. Habilitar "PageSpeed Insights API"
3. "Create Credentials → API key", restringir a esa API
4. Pegar en `docker/env/dev-cli/.{env}` con el formato
   `PSI_API_KEY=<tu_key_aqui>` (sin comillas).
5. El tool resuelve la key en runtime via `grep -m1 '^PSI_API_KEY='`
   del archivo del env activo (NUNCA carga el `.env` completo —
   cumple [env-files.md](../../rules/env-files.md))

Sin la key, `lighthouse_psi` reporta `SKIPPED` y el run continua con
isitagentready + validators. El audit total NO falla.

## Retry + bloqueos (scraper.py)

- 3 retries con backoff exponencial: 5s, 15s, 45s.
- BlockedError ante http 403/429/5xx o timeout.
- ParseError ante shape JSON invalido.
- Hard guard en `run_audit`: cualquier excepcion no contemplada en
  `_scrape_with_retry` se captura y degrada a ERROR result. UN fallo
  de un (target, tool) NUNCA aborta el run global.
- Pausa de 5s entre tools del mismo target.
- Pausa de 2s entre targets.

Ver [04-troubleshooting.md](../../docs/ai-audit/04-troubleshooting.md).

## Reglas duras (de la rule)

- SIEMPRE prod como fuente de verdad. dev = falsos negativos.
- SIEMPRE `PSI_API_KEY` en `docker/env/dev-cli/.{env}`. NUNCA en
  client/server/SSM.
- SIEMPRE reportes a `tmp/ai-audit/`. NUNCA a `docs/`.
- NUNCA correr en CI/CD (rompe ToS de PSI/isitagentready por frecuencia).
- NUNCA commitear `tmp/` ni el `.env` con la key.

## Tools descartadas (mayo 2026)

| Tool | Razon |
|------|-------|
| aibotchecker.online | No API publica + "free check" requiere signup; overlap 99% con isitagentready |
| Ahrefs AI Visibility | API key cuesta $500+/mes (Brand Radar); webapp gratis sin endpoint JSON |
| Semrush AI Visibility | API key cuesta $499+$99/mes; free tier sin acceso a API |
| Cloro (cloro.dev) | Anunciado como free pero requiere API key + Hobby $100/mes |
| HubSpot AEO Grader | Brand-based (no URL-based) + reCAPTCHA en form |

Detalle en [01-tools-evaluadas.md](../../docs/ai-audit/01-tools-evaluadas.md).

## Anti-patrones

- Auditar dev como gate de PR (ese env bloquea AI crawlers
  por diseno).
- Confiar solo en isitagentready (no mide performance ni JSON-LD
  Person en el HTML rendered).
- Bloquear el run si un tool falla (las 3 son ortogonales y
  scraper.py tiene hard guard).
- Implementar tracker historico JSONL en MVP (scope creep).

## Ceiling intencional del score (mayo 2026)

isitagentready se queda en 3-4/5 INTENCIONALMENTE. El portfolio NO publica
`/.well-known/openid-configuration` ni `/.well-known/oauth-protected-resource`
porque no tiene auth real. Publicar stubs OAuth es anti-pattern.

Para subir de 2/5 a 3-4/5 se implemento (plan
`docs/specs/ai-audit-level-3-4/`, mergeado en `feature/ai-audit-level-3-4`):

1. Fix bug Cloudflare Pages SPA fallback en `/.well-known/api-catalog`
   (renombrar a `.json` + rewrite 200 en `_redirects`).
2. Markdown estatico: postbuild genera `.md` gemelo por cada `index.html`
   via `@portfolio/markdown-export` (turndown + GFM).
3. Cloudflare Transform Rule reescribe `Accept: text/markdown` -> `.md`
   (ver `cloudflare/transform-rules.md`).
4. MCP server `/mcp` en cada niche via Pages Functions (paquete
   `@portfolio/mcp` con 3 tools: `get_cv_section`, `list_projects`,
   `search_experience`).
5. MCP server card publico `/.well-known/mcp/server-card.json`
   (builder `packages/seo/src/lib/build-mcp-server-card.ts`).

NO subir de 4/5 publicando stubs OAuth. Cualquier propuesta en esa
direccion se rechaza.

## Documentos relacionados

- Rule autoritativa: [.claude/rules/ai-audit.md](../../rules/ai-audit.md)
- Docs detallados: [.claude/docs/ai-audit/](../../docs/ai-audit/)
  - [README.md](../../docs/ai-audit/README.md) — indice
  - [01-tools-evaluadas.md](../../docs/ai-audit/01-tools-evaluadas.md)
  - [02-auth-setup.md](../../docs/ai-audit/02-auth-setup.md)
  - [03-arquitectura.md](../../docs/ai-audit/03-arquitectura.md)
  - [04-troubleshooting.md](../../docs/ai-audit/04-troubleshooting.md)
- Rule env-files: [.claude/rules/env-files.md](../../rules/env-files.md)
  (politica de NO leer `.env` completos)
