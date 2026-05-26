# 10 — Commits

> **Anterior**: [09-fase-3-validar-skills.md](09-fase-3-validar-skills.md) · **Siguiente**: [11-paralelizacion-worktrees.md](11-paralelizacion-worktrees.md)

## Secuencia de commits

Cada commit deja el repo verde (lint + typecheck + tests del scope) y
ejecuta su verificacion incremental ANTES de commitear. NO se difiere
verificacion al final (eso es el cierre de Fase 4).

| # | Commit | Fase | Cubre AC | Verificacion |
|---|--------|------|----------|--------------|
| 1 | `docs(specs): plan ai-audit-level-3-4 (carpeta inicial)` | Plan setup | — | `biome check docs/specs/ai-audit-level-3-4/` |
| 2 | `docs(specs): fase 0 - diagnostico bug SPA fallback en api-catalog` | 0 | AC-0 | `biome check` + reproduccion local con wrangler |
| 3 | `fix(seo): sirve api-catalog como .json + rewrite 200 desde URL canonica` | 1A | AC-1, AC-2 | tests verde + `wrangler pages dev` local |
| 4 | `feat(markdown-export): paquete que convierte HTML del dist a Markdown via turndown` | 1B | AC-4 | tests verde + coverage >= 80% |
| 5 | `feat(apps): postbuild genera .md gemelo por cada index.html` | 1B | AC-3, AC-5 | build de 6 apps genera .md |
| 6 | `feat(seo,docs): Content-Type text/markdown para .md + documenta Transform Rule` | 1C | AC-6 | tests + docs |
| 7 | `feat(mcp): paquete @portfolio/mcp con handlers initialize + tools/list` | 2A | AC-7 (parcial) | tests + `wrangler pages dev` |
| 8 | `feat(apps): expone endpoint /mcp en Pages Functions de los 6 niches` | 2A | AC-7 | wrappers + integracion local |
| 9 | `feat(mcp): implementa tools get_cv_section + list_projects + search_experience` | 2B | AC-9, AC-10 | tests + tools/call local |
| 10 | `feat(mcp): handle-tools-call ruta por nombre + error TOOL_NOT_FOUND/TOOL_EXECUTION_ERROR` | 2B | AC-8 | tests cubren error paths |
| 11 | `feat(seo,mcp): publica /.well-known/mcp/server-card.json + Link header` | 2C | AC-11 | server card valido en 6 niches |
| 12 | `docs(rules,skills): documenta ceiling intencional + MCP server endpoint` | 3 | — | matriz claude -p 5/5 PASS |
| 13 | `chore(specs): cierra plan ai-audit-level-3-4 (verificacion E2E completa)` | 4 | AC-12 | bateria E2E (seccion 11) en verde |

## Reglas por commit

- **Cada commit deja el repo verde**: lint + typecheck + tests del
  scope pasan ANTES del commit.
- **Conventional Commits en espanol**: subject < 70 chars, body con
  bullets en imperativo. Sin atribucion IA.
- **Verificacion incremental por commit**: el comando esta en el body
  del archivo de fase correspondiente. NO se difiere al final.
- **Si un commit falla la verificacion**: corregir y crear un commit
  nuevo. NUNCA amend de un commit ya pusheado (no aplica aqui porque
  no se pushea hasta el cierre).
- **El primer commit** es la carpeta del plan (con `README.md` +
  `01-..09.md`, sin codigo). Los archivos 10, 11, 12 del plan se
  agregan al primer commit tambien (son parte del setup).
- **El ultimo commit** (Fase 4) ejecuta `git rm -r docs/specs/ai-audit-level-3-4/`
  segun `.claude/rules/plan-format.md` (la carpeta es efimera). El plan
  vivira en git log + PR mergeado.

## Mensaje detallado por commit

### Commit 1: plan inicial

```
docs(specs): plan ai-audit-level-3-4 (carpeta inicial)

- Agrega README.md como indice + estado por fase
- 01: contexto + decision + 12 AC numerados (BDD)
- 02: Fase 0 (diagnostico bug SPA fallback)
- 03: Fase 1A (fix api-catalog: rename + rewrite 200)
- 04: Fase 1B (Markdown estatico via turndown)
- 05: Fase 1C (Cloudflare Transform Rule)
- 06: Fase 2A (MCP server endpoint en Pages Functions)
- 07: Fase 2B (3 tools: get_cv_section, list_projects, search_experience)
- 08: Fase 2C (MCP server card en /.well-known/mcp/)
- 09: Fase 3 (validar skills + rules con claude -p)
- 10: secuencia completa de 13 commits
- 11: paralelizacion con git worktrees
- 12: verificacion E2E iterativa + criterio de cierre
```

### Commit 3: fix api-catalog

```
fix(seo): sirve api-catalog como .json + rewrite 200 desde URL canonica

- Renombra build output a /.well-known/api-catalog.json (evita SPA fallback
  de Cloudflare Pages para rutas sin extension)
- Agrega rewrite 200 en _redirects: /.well-known/api-catalog -> .json
- Actualiza Content-Type a application/linkset+json (RFC 9727 correcto)
- Actualiza Link header del prebuild para apuntar a .json + type declarado
- Tests: 3 nuevos cubren los headers + redirect
- Verifica local con wrangler pages dev: AC-1 + AC-2 OK
- Cubre fix de "API Catalog is not valid JSON" reportado por isitagentready

Refs: docs/specs/ai-audit-level-3-4/03-fase-1a-fix-api-catalog.md
```

### Commit 13: cierre del plan

```
chore(specs): cierra plan ai-audit-level-3-4 (verificacion E2E completa)

- Elimina la carpeta docs/specs/ai-audit-level-3-4/ (era efimera)
- Verificacion E2E (Fase 4): lint + typecheck + unit + coverage + build
  + ai_audit local contra dev (con cambios deployados)
- Resultado ai_audit local contra dev: avg X/100 (baseline 74.83)
- isitagentready: Y/5 en N de 6 niches (baseline 2/5)
- validators: Z/100 (baseline 88)

Refs: PR #<num> a dev (que promovera a stage y main)
```

## PR final

Un solo PR `feature/ai-audit-level-3-4 -> dev`. El body usa el template
de `.claude/rules/git-workflow.md` (Problema / Solucion / Como probar /
TODO) y reutiliza la bateria de Fase 4 como "Como probar".

Despues del merge a dev:
1. Esperar deploy a dev OK.
2. Correr `ai_audit --env=dev` (los cambios deberian aparecer en
   validators + mcp + api-catalog; isitagentready sigue 2/5 contra dev
   porque dev bloquea AI bots por diseno, NO contra ese).
3. Promover dev -> stage -> main (PRs separados).
4. Correr `ai_audit` final contra prod. AC-12 debe pasar.
