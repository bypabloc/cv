# Spec: ai-audit-tool

> Plan de implementacion del script `devtools/ai_audit`: scraper de
> 4 herramientas externas de AI readiness (isitagentready.com,
> aibotchecker.online, Ahrefs AI Visibility, Semrush AI Visibility)
> via Playwright Python, con snapshot JSON + reporte Markdown por
> niche y env.
>
> **Rama**: `feature/ai-audit-devtools` (partiendo de `dev`).
> **Audiencia**: el orquestador (Claude + dev) que ejecuta este plan.
> **Vida util**: efimero — se elimina al mergear a `dev` (ver
> `.claude/rules/plan-format.md` -> "Ciclo de vida de la carpeta del
> plan").

## Estado por fase

| Fase | Archivo | Estado |
|------|---------|--------|
| 1 | [01-contexto-y-decision.md](01-contexto-y-decision.md) | escrita |
| 2 | [02-fase-scaffold.md](02-fase-scaffold.md) | pendiente |
| 3 | [03-fase-auth.md](03-fase-auth.md) | pendiente |
| 4 | [04-fase-tools.md](04-fase-tools.md) | pendiente |
| 5 | [05-fase-report.md](05-fase-report.md) | pendiente |
| 6 | [06-fase-cli.md](06-fase-cli.md) | pendiente |
| 7 | [07-fase-docs-permanentes.md](07-fase-docs-permanentes.md) | escrita (commit 1) |
| 8 | [08-commits.md](08-commits.md) | secuencia commiteable |
| 9 | [09-paralelizacion-worktrees.md](09-paralelizacion-worktrees.md) | tabla worktrees |
| 10 | [10-verificacion-e2e.md](10-verificacion-e2e.md) | bateria de cierre |

## Cuando leer

| Documento | Cuando leer |
|-----------|-------------|
| 01 | Antes de cualquier otra cosa: decisiones no-reabribles |
| 02 | Antes del primer commit de codigo (scaffold) |
| 03 | Antes de implementar `auth.py` + subcomando setup |
| 04 | Antes de implementar los 4 scrapers en `tools/` |
| 05 | Antes de implementar `report.py` (render JSON + Markdown) |
| 06 | Antes de wire al CLI (`devtools/run.py` registry) |
| 07 | Ya esta entregado (commit 1) — los archivos `.claude/` y este plan |
| 08 | Para ver la secuencia de commits que el plan produce |
| 09 | Para paralelizar via git worktrees (los 4 scrapers son disjuntos) |
| 10 | Antes del push + PR: bateria E2E de cierre (gate del PR) |

## Decisiones no-reabribles (de la conversacion previa)

1. **4 tools auditadas**: isitagentready + aibotchecker + Ahrefs +
   Semrush.
2. **Env**: configurable via flag `--env=<dev|stage|prod>`, default
   prod. dev/stage son falsos negativos por diseno (bloquean
   crawlers).
3. **Output**: snapshot JSON + Markdown report en
   `tmp/ai-audit/<timestamp>/`. NO time-series, NO commit del
   reporte.
4. **Trigger**: manual on-demand. NUNCA en CI/CD.
5. **Auth**: cuentas free + Playwright storageState en
   `docker/env/dev-cli/ai-audit/<tool>.json` (LOCAL-ONLY,
   gitignored). Subcomando `ai_audit setup --tool=<X>`.
6. **Granularidad capturada**: score agregado + categorias + top 5
   fixes accionables.
7. **URLs**: default solo home (root) por niche. Custom via
   `--targets=niche:/path,niche:/path`.
8. **Bloqueos**: retry exp backoff (5s, 15s, 45s) + skip + reporte
   explicito `BLOCKED`/`ERROR`. 3 intentos max.
9. **Playwright runtime**: Python via `uv add playwright` en
   `devtools/.venv`. Auto `playwright install chromium` en primer
   run.
10. **Docs permanentes**: rule + skill + 4 docs van en este mismo
    PR (commit 1) — no se difieren a implementacion.

## Reglas criticas (autoritativa en [`.claude/rules/ai-audit.md`](../../.claude/rules/ai-audit.md))

- SIEMPRE prod como fuente de verdad para decisiones.
- SIEMPRE storageState en `docker/env/dev-cli/ai-audit/`. NUNCA otra
  categoria.
- SIEMPRE reportes a `tmp/ai-audit/`. NUNCA a `docs/`.
- NUNCA correr en CI/CD.
- NUNCA commitear `docker/env/dev-cli/ai-audit/*.json` ni `tmp/`.

## Matriz de verificacion (resumen)

| Etapa | Verificacion |
|-------|--------------|
| Cada commit | `python -m compileall -q devtools/ai_audit` + ruff check |
| Tests por modulo | `pytest devtools/tests/unit/src/ai_audit/test_<modulo>.py` |
| Coverage | `>= 80%` per-file en archivos creados/modificados |
| Smoke E2E | `python devtools/run.py ai_audit --tools=isitagentready --niches=generic` (1 audit real) |
| Gate del PR | Bateria completa de [10-verificacion-e2e.md](10-verificacion-e2e.md) |

## Navegacion

- [01 Contexto y decision](01-contexto-y-decision.md)
- [10 Verificacion E2E](10-verificacion-e2e.md)
- Rule permanente: [`.claude/rules/ai-audit.md`](../../.claude/rules/ai-audit.md)
- Skill: [`.claude/skills/ai-audit/SKILL.md`](../../.claude/skills/ai-audit/SKILL.md)
- Docs: [`.claude/docs/ai-audit/`](../../.claude/docs/ai-audit/)
