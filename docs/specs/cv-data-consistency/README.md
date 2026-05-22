# Plan: Consistencia de datos del CV (profile_niches + stats + summary + CV genérico)

> Corrige las 3 discrepancias CRÍTICAS detectadas en la auditoría de
> consistencia de datos del CV y enriquece el render del CV genérico para
> que muestre más detalle (achievements + responsabilidades completas) que
> los CV de nicho. Scope Medium: toca content + DB + migración + seed + un
> componente compartido.

## Cuándo leer cada documento

| Documento | Cuándo leer |
|-----------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Secciones 1-3: contexto, solución, criterios de aceptación |
| [02-fase-stats-summary.md](02-fase-stats-summary.md) | Fase 1: corregir `profile.stats` + `summary` desactualizado |
| [03-fase-profile-niches-db.md](03-fase-profile-niches-db.md) | Fase 2: tabla `profile_niches` + modelo + migración Alembic + seed |
| [04-fase-cv-generico.md](04-fase-cv-generico.md) | Fase 3: enriquecer el render del CV genérico (achievements + bullets) |
| [05-commits.md](05-commits.md) | Sección 9: listado de commits incrementales |
| [06-paralelizacion-worktrees.md](06-paralelizacion-worktrees.md) | Sección 10: git worktrees worktree-safe |
| [07-verificacion-e2e.md](07-verificacion-e2e.md) | Sección 11: verificación E2E iterativa (gate del PR) |

## Estado por fase

| Fase | Documento | Estado |
|------|-----------|--------|
| 1 — stats + summary | `02-fase-stats-summary.md` | pending |
| 2 — profile_niches en DB | `03-fase-profile-niches-db.md` | pending |
| 3 — CV genérico enriquecido | `04-fase-cv-generico.md` | pending |
| 4 — verificación E2E | `07-verificacion-e2e.md` | pending |

## Decisiones no reabribles

| # | Decisión | Razón |
|---|----------|-------|
| D-1 | `profile.niches` se persiste en una tabla `profile_niches` nueva | El usuario decidió que la DB sea fuente de verdad completa del CV |
| D-2 | `stats.companies = 5` | 5 nombres de empresa distintos en los YAML; "Independiente / Académico" cuenta como una |
| D-3 | `stats.yearsExperience = 12` se mantiene; lo que se corrige es el `summary` | El usuario confirmó 12 años reales; el `summary` ("8 años") quedó desactualizado |
| D-4 | `stats.countries = 4` se mantiene, con comentario | Venezuela + Perú (Dibal) + Chile + México (Destacame) = 4 países reales |
| D-5 | El enriquecimiento de contenido (texto nuevo) NO entra en este plan | Requiere input del usuario; este plan solo reorganiza lo que ya existe. El cuestionario de feedback se entrega aparte |
| D-6 | `CvSections` muestra detalle completo solo para `niche === 'generic'` | El usuario quiere que el CV genérico sea el más detallado; los niches muestran un subset |

## Reglas críticas del plan

- TDD obligatorio: tests primero en la Fase 1 y 3 (lógica nueva).
- La migración Alembic NO se edita: la 81c2cc51db34 ya está aplicada en
  prod. Se crea una migración NUEVA encadenada (`down_revision` apunta a
  81c2cc51db34).
- El `downgrade()` de la migración nueva debe revertir EXACTAMENTE el
  `upgrade()`.
- Cada commit deja el repo verde (lint + typecheck + tests del scope).
- El último commit es la Fase 4 (verificación E2E) e incluye el
  `git rm -r docs/specs/cv-data-consistency/`.

## Matriz de verificación

| Fase | Verificación |
|------|--------------|
| 1 | `pnpm --filter @portfolio/content exec vitest run` + `pnpm --filter @portfolio/app-shared exec vitest run` + typecheck |
| 2 | `python -m compileall serverless/lambda/shared/db` + migración aplica `upgrade`+`downgrade` en branch Neon de prueba |
| 3 | `pnpm --filter @portfolio/app-shared exec vitest run` + `pnpm run build` + preview visual |
| 4 | Batería completa: lint + typecheck + unit + build + E2E Playwright |

## Navegación

Empezar por [01-contexto-y-decision.md](01-contexto-y-decision.md).
