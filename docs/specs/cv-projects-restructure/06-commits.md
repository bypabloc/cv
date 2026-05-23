# Seccion 9: Commits

> Secuencia de commits en `feature/cv-projects-restructure`. Cada uno
> deja el repo verde y verifica su scope incremental.

## Lista

| # | Mensaje | AC | Verify incremental |
|---|---------|----|--------------------|
| 1 | `docs(specs): plan cv-projects-restructure` | — | Carpeta creada con 9 archivos |
| 2 | `feat(content): extender ProjectSchema con links y ExperienceSchema con summary` | AC-2, AC-8, AC-10 | `pnpm exec tsc --noEmit && pnpm --filter @portfolio/content exec vitest run` |
| 3 | `feat(seeds): eliminar cv-builder y portfolio-astro de seeds de proyectos` | AC-1 | `ls serverless/lambda/services/db/core/seeds/data/projects/ \| wc -l` -> 4 |
| 4 | `feat(seeds): reescribir 4 proyectos con links multiples y priority` | AC-1, AC-2 | `python devtools/run.py serverless run --stage=dev --lambda=db --event=events/seed.json` ok |
| 5 | `feat(seeds): agregar summary bilingue a 9 experiences` | AC-8 | seed ok + cache regenerado |
| 6 | `chore(content): regenerar data-cache desde seed dev` | AC-1, AC-8 | `node scripts/fetch-cv-cache.mjs` |
| 7 | `feat(ui): renombrar Proyectos destacados a Proyectos` | — | grep "destacados" no encuentra en ui/i18n |
| 8 | `feat(ui): mover casos de estudio a ProjectDetail` | AC-3, AC-4 | astro check + visual |
| 9 | `feat(ui): render multi-link en ProjectBentoCard y ProjectDetail` | AC-2 | astro check + visual |
| 10 | `feat(nav): dropdown con 5 niches reemplaza Otras vistas` | AC-5 | astro check + a11y check |
| 11 | `fix(hub): hero intro full-bleed background + texto reducido` | AC-6 | visual + viewport check |
| 12 | `feat(ui): TimelineItem muestra summary en home` | AC-8, AC-9 | astro check + visual |
| 13 | `fix(track): <causa raiz a definir>` | AC-7 | `curl -X POST .../track` devuelve 204 |
| 14 | `chore(specs): borrar docs/specs/cv-projects-restructure` | — | bateria seccion 11 verde |

## Regla por commit

Antes de cada commit:

```bash
pnpm exec biome check .
pnpm exec tsc --noEmit
# si el cambio toca .astro:
pnpm exec astro check
# si el cambio toca tests existentes:
pnpm exec vitest run --changed
```

Si el commit toca archivos `.py` (serverless seeds o handlers):

```bash
cd serverless/lambda
.venv/bin/ruff check .
.venv/bin/python -m compileall -q services/db services/tracking_pixel
```

## PR

Un solo PR `feature/cv-projects-restructure -> dev`. Body con resumen de
los 14 commits, link a cada AC y "Como probar" reutilizando los
comandos de la seccion 11.
