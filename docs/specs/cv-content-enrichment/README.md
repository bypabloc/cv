# Plan: Enriquecimiento de contenido del CV (plan B)

> Enriquece el contenido de los 5 CV de nicho: logros con métricas por
> nicho, campo `country` estructurado, reestructuración de 4 experiencias
> hoy agrupadas, summary por nicho, páginas de detalle por experiencia y
> por proyecto, case studies para los 6 proyectos, y un proyecto nuevo
> (cv). Scope Large.

## Origen

Surge del cuestionario de feedback posterior al plan A
(`cv-data-consistency`, ya implementado). El usuario respondió 15
preguntas que definen el alcance. Este plan es la **fase de contenido**:
el plan A corrigió datos rotos, este enriquece el contenido.

## Cuándo leer cada documento

| Documento | Cuándo leer |
|-----------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Secciones 1-3: contexto, solución, criterios de aceptación |
| [02-fase-schema-zod.md](02-fase-schema-zod.md) | Fase 1: schema Zod (`country`, `metricsEstimated`) en `@portfolio/content` |
| [03-fase-db-migracion.md](03-fase-db-migracion.md) | Fase 2: migración Alembic + modelos SQLAlchemy + seed para `country` y `metrics_estimated` |
| [04-fase-experiencias.md](04-fase-experiencias.md) | Fase 3: reestructurar las 4 experiencias + `country` + logros por nicho en las 9 |
| [05-fase-proyectos.md](05-fase-proyectos.md) | Fase 4: case study + métricas en los 6 proyectos + proyecto `cv` nuevo |
| [06-fase-summary-nicho.md](06-fase-summary-nicho.md) | Fase 5: summary por nicho en los YAML i18n curriculum |
| [07-fase-paginas-detalle.md](07-fase-paginas-detalle.md) | Fase 6: páginas `/experience/<slug>` y `/projects/<slug>` en las 6 apps |
| [08-commits.md](08-commits.md) | Sección 9: listado de commits |
| [09-paralelizacion-worktrees.md](09-paralelizacion-worktrees.md) | Sección 10: git worktrees |
| [10-verificacion-e2e.md](10-verificacion-e2e.md) | Sección 11: verificación E2E iterativa (gate del PR) |
| [11-metricas-estimadas.md](11-metricas-estimadas.md) | Anexo: TODAS las cifras inventadas para que el usuario las valide |

## Estado por fase

| Fase | Documento | Estado |
|------|-----------|--------|
| 1 — schema Zod | `02-fase-schema-zod.md` | pending |
| 2 — DB (migración Alembic) | `03-fase-db-migracion.md` | pending |
| 3 — experiencias | `04-fase-experiencias.md` | pending |
| 4 — proyectos | `05-fase-proyectos.md` | pending |
| 5 — summary por nicho | `06-fase-summary-nicho.md` | pending |
| 6 — páginas de detalle | `07-fase-paginas-detalle.md` | pending |
| 7 — verificación E2E | `10-verificacion-e2e.md` | pending |

## Decisiones no reabribles (del cuestionario del usuario)

| # | Decisión | Origen |
|---|----------|--------|
| D-1 | Las experiencias se reorientan por nicho: el contenido de cada experiencia enfatiza el ángulo del nicho (en fintech el rol fintech, en architect la arquitectura, en leader el liderazgo) | P1 |
| D-2 | Se generan **logros con métricas inventadas plausibles** para experiencias y proyectos. Cada entry con cifras estimadas lleva `metricsEstimated: true` (campo interno, NO se renderiza). El anexo `10-metricas-estimadas.md` lista todas para que el usuario las valide | P2, P7, P9 |
| D-3 | En cada nicho, las experiencias irrelevantes (universidad, Cofasa en fintech) NO se ocultan: se muestran al final como experiencia antigua, con su página de detalle accesible | P3 |
| D-4 | El CV genérico muestra TODAS las responsabilidades (sin tope) | P4 — ya implementado en plan A |
| D-5 | Las 4 experiencias "Independiente / Académico" se separan: cada una con su contexto real (institución, tipo de proyecto, país) | P5 |
| D-6 | Cada experiencia y cada proyecto tiene una **página de detalle** en path propio (`/experience/<slug>`, `/projects/<slug>`). Las recientes muestran el detalle también en la tarjeta del home; las antiguas, resumen en el home + botón al detalle. TODAS tienen botón al detalle | P6, P8 |
| D-7 | Los 6 proyectos tienen tarjeta resumen + `caseStudyDetailed` + `metrics` (case studies inventados y mejorados) | P8, P9 |
| D-8 | Se agrega el proyecto `cv` (repo `github.com/bypabloc/cv`) | P10 |
| D-9 | `references`, `languages`, `education` NO se filtran por nicho (se quedan sin `niches`) | P11 |
| D-10 | `publications/` se deja vacía | P12 |
| D-11 | Se agrega campo `country` estructurado a cada experiencia; `stats.countries` pasa a derivarse de ese campo | P13 |
| D-12 | El `summary` es por nicho: vive en `curriculum/<nicho>.{es,en}.yaml`; si un nicho no lo define, hereda el `_base`; el `summary` de `profile.ts` queda como fallback global | P14 |
| D-13 | El CV en inglés se redacta con tono para mercado US/internacional, NO traducción literal | P15 |
| D-14 | TODOS los textos (generados o editados) usan **español neutro**: sin modismos ni acento de ningún país | Extra |
| D-15 | Los campos nuevos del CV (`country`, `metricsEstimated`) se propagan a la base PostgreSQL con una **migración Alembic nueva** + modelos SQLAlchemy + seed. NO se editan los `serverless/migrations/_archive/*.sql` (archivados, no se aplican, regla `neon-management.md`) | Pedido del usuario + regla del proyecto |

## Reglas críticas del plan

- **Métricas inventadas**: plausibles y conservadoras, nunca exageradas.
  Cada entry afectada lleva `metricsEstimated: true`. El anexo
  `10-metricas-estimadas.md` es de entrega obligatoria — el usuario debe
  poder revisar y corregir cada cifra en un solo lugar.
- El proyecto NO usa content collections de Astro: la data viene de
  `@portfolio/content` (`import { experiences }`). Las páginas de detalle
  usan `getStaticPaths()` con ese import, NO `getCollection()`.
- TDD: tests primero en las fases con lógica nueva (helpers, schema).
- Español neutro en todo texto nuevo. Inglés con tono US.
- Cada commit deja el repo verde. El último es la Fase 6 + el
  `git rm -r docs/specs/cv-content-enrichment/`.
- Las 6 apps deben buildear; las páginas de detalle suman ~180 páginas
  estáticas (15 slugs × 2 locales × 6 apps).

## Matriz de verificación

| Fase | Verificación |
|------|--------------|
| 1 | `vitest` content + `tsc` — schema Zod válido, tests de los campos nuevos |
| 2 | `compileall` backend + 310 tests `shared` + migración Alembic `upgrade`/`downgrade` (`--sql` o branch Neon) |
| 3 | `vitest` content — las 9 experiencias parsean; paridad de slugs YAML |
| 4 | `vitest` content — los 6 proyectos + `cv` parsean |
| 5 | `vitest` content + app-shared — merge del summary por nicho |
| 6 | `pnpm run build` — las 6 apps generan las páginas de detalle sin error |
| 7 | Batería completa: lint + typecheck + unit + build + E2E Playwright |

## Navegación

Empezar por [01-contexto-y-decision.md](01-contexto-y-decision.md).
