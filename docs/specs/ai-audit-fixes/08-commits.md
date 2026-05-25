# 08 - Commits

[< 07 Validar skills](07-fase-validar-skills.md) | [09 Worktrees >](09-paralelizacion-worktrees.md)

Listado de commits incrementales. Cada uno deja repo verde (lint +
typecheck + tests del scope). Conventional Commits en espanol.

| # | Commit | Scope | Que cubre |
|---|--------|-------|-----------|
| 1 | `docs(specs): plan ai-audit-fixes` | docs only | Crear `docs/specs/ai-audit-fixes/` (este plan). Commit YA HECHO al inicio. |
| 2 | `feat(packages/seo): builders api-catalog + redirects + website-schema + link headers` | packages/seo + tests | Fase 1: 3 builders nuevos + buildHeaders actualizado + tests. |
| 3 | `fix(packages/ui): subir text-muted y text-subtle a WCAG AA` | packages/ui | Fase 2: 2 tokens. |
| 4 | `feat(devtools/ai_audit): validator detecta Cloudflare-managed robots + sitemap-index fallback` | devtools + tests | Fase 3: validators con `neutral` status + scoring half + tests. |
| 5 | `feat(apps): prebuild genera _redirects + api-catalog` | apps/*/scripts (6) | Fase 4: 6 prebuild scripts llaman a los nuevos builders. |
| 6 | `feat(packages/app-shared): incluir WebSite JSON-LD en layout` | packages/app-shared | Fase 5: schema WebSite junto al ProfilePage. |
| 7 | `test(claude): validar skills/rules de ai-audit con claude -p` | (sin codigo) | Fase 6: documentar resultado de los 5 prompts en el commit message. |
| 8 | `chore(specs): cierra plan ai-audit-fixes` | docs only (rm -r) | Fase 9: eliminar `docs/specs/ai-audit-fixes/` + verificacion final. |

## Regla por commit

Cada commit ANTES de cerrarse:

1. `pnpm exec biome check .`
2. `pnpm exec tsc --noEmit && pnpm exec astro check`
3. `pnpm exec vitest run` (paquetes afectados) + `python devtools/run.py test_runner --module=devtools --type=unit` (si tocamos devtools)
4. `pnpm run build` (si tocamos packages/seo o app-shared — afecta build)
5. Coverage >= 80% per-file en archivos modificados.

## Resumen de la secuencia

```text
1. (HECHO) docs(specs): plan + carpeta creada
2. feat(seo): builders + tests + buildHeaders actualizado
3. fix(ui): tokens
4. feat(devtools): validator + tests
5. feat(apps): prebuild scripts
6. feat(app-shared): WebSite JSON-LD
7. test(claude): validacion skills
8. chore(specs): elimina carpeta + verificacion final
```

## PR

Un solo PR: `feature/ai-audit-devtools -> dev`.

Title: `feat(ai-audit): mejoras de readiness IA + SEO (validators 100, lighthouse 100, +3 builders seo)`

Body:

```markdown
## Problema
Audit `ai_audit` daba 63/100 promedio en prod. Fixes accionables
detectados en los 3 tools (isitagentready, validators, lighthouse_psi).

## Solucion
1. packages/seo: 3 builders nuevos (api-catalog, redirects, website-schema) + Link headers
2. packages/ui: tokens text-muted/text-subtle pasan WCAG AA
3. devtools/ai_audit: validator detecta Cloudflare-managed robots como neutral + sitemap-index fallback
4. apps/*/scripts: prebuild genera _redirects + .well-known/api-catalog
5. packages/app-shared: WebSite JSON-LD junto al ProfilePage
6. .claude/* validado con claude -p (5/5 prompts pass)

## Como probar
- `pnpm run build` (los 6 sites verde)
- `python devtools/run.py test_runner --module=devtools --type=unit` (789+ tests)
- Tras merge + deploy: `python devtools/run.py ai_audit` debe dar avg >= 85.
```

[< 07 Validar skills](07-fase-validar-skills.md) | [09 Worktrees >](09-paralelizacion-worktrees.md)
