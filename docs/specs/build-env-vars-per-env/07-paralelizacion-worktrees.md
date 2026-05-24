# 07 — Paralelizacion con git worktrees

> Cuanta paralelizacion real es posible (archivos disjuntos) y cual NO.

## Base secuencial

Commits que TODOS los worktrees necesitan o que tocan archivos
transversales — se ejecutan ANTES de abrir cualquier worktree:

- **Commit 1**: `docs(specs): plan build-env-vars-per-env` — la
  carpeta de la spec es la fuente de verdad que cada worktree consulta.
- **Commit 2**: `feat(app-shared): validateApiEndpoint + validateTurnstileSitekey`
  — define la API publica que consumen el commit 3 (guard en
  TrackingPixel) y el commit 8 (astro.config con buildSiteUrl ya
  existe pero el guard de Turnstile no).

## Tabla de paralelizacion

| Fase | Worktree-safe | Por que / Por que no |
|------|---------------|----------------------|
| Commit 1 | NO (base) | Carpeta del spec — secuencial |
| Commit 2 | NO (base) | Define API que usan 3 y 8 |
| Commits 3+4 | **SI, en pareja** | 3 toca `packages/ui/src/components/TrackingPixel.astro`; 4 toca `packages/ui/tests/build/*` + `vitest.config.ts`. Archivos disjuntos. Worktree A: TrackingPixel guard. Worktree B: build-test. |
| Commit 5 | NO (single file) | `.git-hooks/pre-push` solo — 5 minutos de trabajo, no vale worktree |
| Commits 6+7 | NO (mismo paquete) | 6 escribe `devtools/github_sync/*.py`; 7 escribe `devtools/github_sync/README.md`. Mismo paquete, dependen entre si (el README cita modulos). Mejor secuencial |
| Commits 6 vs 8 | **SI, paralelizable** | 6: `devtools/github_sync/**`. 8: `apps/*/astro.config.ts`. Totalmente disjuntos. Worktree A: github_sync. Worktree B: astro.config x6 (es repetitivo pero rapido). |
| Commits 9+10 | NO (mismo archivo) | Ambos modifican `.github/workflows/deploy-apps.yml`. SECUENCIAL obligatorio (race conditions sobre yaml) |
| Commit 11 | NO | Toca archivos transversales (`.claude/rules/`, `CLAUDE.md`). Hacer al final, secuencial |
| Commit 12 | NO (cierre) | Ultimo commit del plan, incluye `git rm -r docs/specs/...` y la bateria E2E final |

## Lo que NO se paraleliza (resumen)

- Modificaciones al mismo archivo: yaml workflows (commits 9+10), pre-push hook
- Commit 11 (rules + CLAUDE.md): un solo dev, decisiones de redaccion coherentes
- Commit 12 (cierre): la bateria E2E debe correr secuencial contra el repo en
  el estado final, ningun worktree por encima

## Como lanzar un worktree

Patron canonico (de la rule del proyecto):

```bash
# Worktree para Fase 1 commit 4 (build-test) mientras alguien hace commit 3
git worktree add ../portfolio-build-test feature/build-env-vars-per-env

# En el worktree A (build-test):
cd ../portfolio-build-test
pnpm install --frozen-lockfile  # podria usar el mismo node_modules via symlink
# ... implementar el test, commitear con el msg del commit 4 ...

# De vuelta en el principal:
cd -
git pull  # trae el commit del worktree

# Al cerrar:
git worktree remove ../portfolio-build-test
```

## Maxima paralelizacion realista

Plan de 12 commits, hasta 2-3 worktrees concurrentes:

```
Fase setup:     1, 2        -> SECUENCIAL
Fase 1:         3 || 4      -> 2 worktrees
                5           -> SECUENCIAL
Fase 2 y prep:  (6,7) || 8  -> 2 worktrees
Fase 3:         9, 10       -> SECUENCIAL
Fase 4:         11          -> SECUENCIAL
Cierre:         12          -> SECUENCIAL
```

Ahorro practico: ~30-40% del tiempo total si se usa la paralelizacion
en Fase 1 y Fase 2/prep. Para un plan chico (12 commits, ~6h estimadas)
no es critico — un solo dev secuencial tarda ~8h. La paralelizacion
vale si hay dos personas o el dev quiere bloquear menos su context.

## Anti-patrones a evitar

- Lanzar worktree para los commits 9+10 (yaml conflict garantizado)
- Empezar commit 3 antes que el 2 (el guard depende de
  `validateApiEndpoint` que se exporta en el 2)
- Modificar `.git-hooks/pre-push` (commit 5) en un worktree mientras
  otro modifica `package.json` o `pnpm-lock.yaml`
- Hacer commits sin verificacion incremental "porque despues paraleliza"
  — el repo debe estar verde commit a commit, no solo al final
