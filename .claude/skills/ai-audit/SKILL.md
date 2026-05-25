---
name: ai-audit
description: >
  AI readiness audit for the portfolio. Scrapes 4 external tools
  (isitagentready.com by Cloudflare, aibotchecker.online, Ahrefs AI
  Visibility, Semrush AI Visibility) via Playwright Python in
  devtools/.venv, captures scores per niche + env, generates a JSON
  snapshot and a Markdown report with top 5 prioritized fixes. ALWAYS
  invoke this skill BEFORE answering ANY question about: how AI-ready
  the portfolio is, GEO score, agent-readiness, isitagentready.com,
  AI Visibility Checker, scraping LLM SEO tools, comparing AI
  visibility, how to improve crawlability for ClaudeBot/GPTBot, the
  devtools/ai_audit script, ai_audit catalog of tools, ai_audit
  storageState in dev-cli, ai_audit retry/backoff strategy, where the
  ai-audit reports live, or how to run ai_audit setup. NEVER answer
  from training data alone — this portfolio has a consolidated 2026
  audit pipeline (4 tools, retry policy, snapshot format,
  storageState location) that overrides generic advice.
  Use when the user says "ai audit", "ai readiness", "agent ready",
  "agent-readiness", "isitagentready", "is it agent ready",
  "aibotchecker", "ai bot checker", "ai visibility", "ai visibility
  check", "geo audit", "geo score", "auditar IA", "auditoria IA",
  "auditar para IA", "score de IA", "preparado para IA", "preparado
  para LLM", "preparado para crawlers", "que tan preparado para IA",
  "medir IA seo", "que tan visible en chatgpt", "que tan visible en
  claude", "que tan visible en perplexity", "ai_audit", "devtools
  ai_audit", "scrape ai tools", "scraper ai readiness", "playwright
  audit", "auditar prod IA", "compare niche ai score".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
argument-hint: "[--env=prod|stage|dev] [--niches=...] [--tools=...] [--targets=niche:/path,...]"
---

# AI readiness audit del portfolio

## Estado

Skill + rule + docs estan escritos. La implementacion del script
`devtools/ai_audit/` se entrega via el plan
[docs/specs/ai-audit-tool/](../../../docs/specs/ai-audit-tool/) (rama
`feature/ai-audit-devtools`). Hasta mergear ese plan, los comandos
`python devtools/run.py ai_audit ...` NO existen.

Esta skill responde sobre el DISENO y CONTRATO ya definido; cuando
el plan se mergee, los comandos seran ejecutables.

## Cuando invocar (regla maestra)

Cualquier pregunta sobre "que tan preparada esta esta pagina para
IA", AI/LLM SEO, GEO score, crawlers de IA, score de
isitagentready/aibotchecker/Ahrefs/Semrush, o como ejecutar /
configurar / interpretar el script `ai_audit` -> invocar esta skill.

NO invocar para:
- SEO tradicional (Google Search Console, Lighthouse SEO) -> skill
  `astro-portfolio`
- Tecnicas white/grey/black-hat de AI SEO -> skill
  `ai-prompt-optimization`
- Estrategia general del portfolio -> skill `modern-portfolios`

## Las 4 tools auditadas

| Tool | URL | Auth | Mide |
|------|-----|------|------|
| Is Your Site Agent-Ready? | https://isitagentready.com | Anonima | 5 categorias: Discoverability, Content Accessibility, Bot Access Control, Protocol Discovery, Commerce Standards |
| AI Visibility Checker | https://aibotchecker.online | Anonima | 60+ checks per-bot (GPTBot, ClaudeBot, etc.) + severidad |
| Ahrefs AI Visibility Checker | https://ahrefs.com/ai-visibility-checker | Cuenta gratis | Brand mentions en ChatGPT, Gemini, Perplexity, Copilot, Google AI Overviews |
| Semrush AI Visibility Audit | https://www.semrush.com/ai-visibility-audit | Cuenta gratis | Technical blocking + content audit + AI readiness score + trafico real desde IA |

Detalle por tool (que parsea el scraper, gotchas, frecuencia de
breakage): [01-tools-evaluadas.md](../../docs/ai-audit/01-tools-evaluadas.md).

## Comandos canonicos

```bash
# Audit default: 6 homes de prod, las 4 tools
python devtools/run.py ai_audit

# Subset de niches
python devtools/run.py ai_audit --niches=hub,fintech

# Custom targets (niche + path)
python devtools/run.py ai_audit \
  --targets=architect:/projects,leader:/about

# Subset de tools (skip las que requieren login)
python devtools/run.py ai_audit \
  --tools=isitagentready,aibotchecker

# Setup de auth (1 vez por tool, abre browser interactivo)
python devtools/run.py ai_audit setup --tool=ahrefs
python devtools/run.py ai_audit setup --tool=semrush

# Re-render del Markdown desde un snapshot JSON existente
python devtools/run.py ai_audit report \
  --snapshot=tmp/ai-audit/2026-05-25T10-30-00/snapshot.json
```

## Output

```text
tmp/ai-audit/<timestamp>/
├── snapshot.json     # crudo: por (target, tool) -> score + categorias + top 5 fixes
├── report.md         # human-readable: tabla comparativa + top fixes priorizados
└── runs/             # logs por scraper, screenshots de error si BLOCKED
    ├── <target>_<tool>.log
    └── <target>_<tool>_error.png
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
      "status": "OK",  // OK | PARTIAL | BLOCKED | ERROR | SKIPPED
      "score": 78,
      "categories": {"Discoverability": 90, "Bot Access Control": 60},
      "fixes": [
        {
          "severity": "high",
          "category": "Bot Access Control",
          "issue": "robots.txt missing GPTBot allow rule",
          "fix": "Add `User-agent: GPTBot\\nAllow: /` to robots.txt",
          "file": "apps/generic/public/robots.txt"
        }
      ]
    }
  ]
}
```

## Auth setup (Ahrefs + Semrush)

Las 2 tools que requieren cuenta gratis. Flujo:

1. `python devtools/run.py ai_audit setup --tool=ahrefs` abre browser
   Playwright NO-headless.
2. Logueas manualmente (cuenta gratis sirve).
3. El script detecta el login y persiste cookies a
   `docker/env/dev-cli/ai-audit/ahrefs.json`.
4. Los runs siguientes reusan ese storageState.
5. Cuando expira la sesion: re-correr `setup`.

`docker/env/dev-cli/ai-audit/` esta gitignored (categoria `dev-cli`,
LOCAL-ONLY, NUNCA sincronizada a remoto). Ver
[02-auth-setup.md](../../docs/ai-audit/02-auth-setup.md).

## Retry + bloqueos

- 3 retries con backoff exponencial: 5s, 15s, 45s.
- Reintenta ante 4xx (excepto 401/403 logicos), 5xx, timeout, y
  Cloudflare challenge detectado por presencia de
  `cf-challenge-form` en el DOM.
- Tras 3 intentos sin exito: target marcado como `BLOCKED` en el
  reporte y se continua con el siguiente.
- Pausa de 5s entre tools del mismo target.
- Pausa de 2s entre targets.

Ver [04-troubleshooting.md](../../docs/ai-audit/04-troubleshooting.md)
para sintomas comunes y como diagnosticar.

## Reglas duras (de la rule)

- SIEMPRE prod como fuente de verdad. dev/stage = falsos negativos.
- SIEMPRE storageState en `docker/env/dev-cli/ai-audit/`. NUNCA en
  client/server/SSM.
- SIEMPRE reportes a `tmp/ai-audit/`. NUNCA a `docs/`.
- NUNCA correr en CI/CD (rompe ToS por frecuencia).
- NUNCA commitear `tmp/` ni los `.json` de storageState.

## Anti-patrones (resumen)

- Auditar dev/stage como gate de PR (esos envs bloquean AI crawlers
  por diseno).
- Confiar solo en isitagentready (mide standards, ignora brand
  mentions).
- Bloquear el run si un tool falla (las 4 son ortogonales).
- Implementar tracker historico JSONL en MVP (scope creep).

## Documentos relacionados

- Rule autoritativa: [.claude/rules/ai-audit.md](../../rules/ai-audit.md)
- Docs detallados: [.claude/docs/ai-audit/](../../docs/ai-audit/)
  - [README.md](../../docs/ai-audit/README.md) — indice
  - [01-tools-evaluadas.md](../../docs/ai-audit/01-tools-evaluadas.md)
  - [02-auth-setup.md](../../docs/ai-audit/02-auth-setup.md)
  - [03-arquitectura.md](../../docs/ai-audit/03-arquitectura.md)
  - [04-troubleshooting.md](../../docs/ai-audit/04-troubleshooting.md)
- Plan de implementacion (efimero): [docs/specs/ai-audit-tool/](../../../docs/specs/ai-audit-tool/)
