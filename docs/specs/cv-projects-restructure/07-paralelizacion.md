# Seccion 10: Paralelizacion con git worktrees

## Base secuencial (NO paralelizable)

Los commits 1-6 deben hacerse en orden estricto en una sola rama porque:

- Commit 2 modifica el schema (todos los demas dependen de el).
- Commits 3, 4, 5 modifican seeds (el seed debe correr DESPUES de
  todos los YAML actualizados).
- Commit 6 regenera el cache (depende del seed corrido en commit 5).

## Worktrees safe (post-commit 6)

A partir del commit 6, las siguientes fases tocan archivos disjuntos y
SE PUEDEN paralelizar:

| Fase | Archivos | Paralelizable con |
|------|----------|-------------------|
| Fase 4 (commits 7-9): UI proyectos + casos estudio | `packages/ui/src/components/Project*.astro`, `packages/app-shared/src/components/{CvSections,ProjectDetail}.astro` | Fase 6 |
| Fase 5 (commit 10): Nav dropdown | `packages/ui/src/components/{Nav,NicheDropdown}.astro`, `packages/app-shared/src/lib/define-site-config.ts` | Fase 6, 7, 8 |
| Fase 6 (commit 11): Hub hero | `apps/hub/src/pages/index.astro`, `packages/content/src/data/i18n/hub-selector/*.yaml` | Fase 4, 5, 7, 8 |
| Fase 7 (commit 12): TimelineItem | `packages/ui/src/components/TimelineItem.astro`, `packages/app-shared/src/components/CvSections.astro` (region experience) | Fase 5, 6, 8 |
| Fase 8 (commit 13): /track fix | `serverless/lambda/services/tracking_pixel/**`, DynamoDB ops | Fase 4, 5, 6, 7 |

## Colision conocida

Fase 4 (commit 7-9) y Fase 7 (commit 12) ambos tocan
`packages/app-shared/src/components/CvSections.astro` (Fase 4 elimina
`.case-studies`, Fase 7 cambia el TimelineItem render). Resolver
secuencialmente (NO en paralelo) o consolidar ambos cambios en un solo
worktree.

## Lanzamiento de worktrees (opcional)

Si se decide paralelizar:

```bash
git worktree add ../portfolio-fase5 feature/cv-projects-restructure
git worktree add ../portfolio-fase6 feature/cv-projects-restructure
# trabajar en paralelo, merge a la rama unica al final con git pull en
# cada worktree y rebase contra el ultimo commit de la rama base
```

Para este plan, lanzarse al implementador es opcional: la suite cabe en
una sola sesion sin worktrees, evitando el overhead de coordinar
multiples copies del repo. Recomendado: hacerlo secuencial en una sola
rama.
