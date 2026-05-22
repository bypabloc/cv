# Sección 10 — Paralelización con git worktrees

[← Commits](05-commits.md) · [Verificación E2E →](07-verificacion-e2e.md)

## Base secuencial

El **Commit 1** (la carpeta del plan) es la base secuencial: todo worktree
parte de ahí. No hay archivos transversales compartidos entre las fases —
ver tabla de colisiones abajo.

## Tabla de fases worktree-safe

Las 3 fases de implementación tocan conjuntos de archivos **disjuntos**,
así que pueden ejecutarse en paralelo en worktrees separados tras el
Commit 1:

| Fase / Commit | Archivos | Colisión con otra fase |
|---------------|----------|------------------------|
| Commit 2 (Fase 1) | `packages/content/src/data/profile.ts`, `packages/app-shared/tests/unit/lib/build-stats.test.ts` | Ninguna |
| Commits 3+4 (Fase 2) | `serverless/lambda/shared/db/models/profile.py`, `models/__init__.py`, `base.py`, migración nueva, `db/cv/seed/seed_from_yaml.py` | Ninguna |
| Commit 5 (Fase 3) | `packages/app-shared/src/lib/cv-detail.ts` (nuevo), `cv-detail.test.ts` (nuevo), `packages/app-shared/src/components/CvSections.astro`, `elements.{es,en}.yaml`, posible `schemas.ts` | Ninguna |

Análisis de los 3 checks:

- **File Exclusivity**: los 3 conjuntos no comparten ningún archivo. La
  Fase 1 toca `content/data/profile.ts`; la Fase 3 toca `content/data/
  i18n/elements/*` y posiblemente `content/src/schemas.ts` — archivos
  distintos dentro de `content/`, sin solape.
- **Interface Stability**: la Fase 3 importa `Niche` de `@portfolio/
  content` (tipo estable, no lo modifica). La Fase 1 no cambia ninguna
  interfaz pública. La Fase 2 es backend Python, aislada del frontend.
- **Bounded Scope**: cada fase tiene su Definition of Done acotada en su
  documento.

## Lo que NO se paraleliza

- **Commit 1** (base secuencial): debe estar antes de lanzar worktrees.
- **Commit 6 / Fase 4** (verificación E2E): corre sobre el código de las
  3 fases ya integradas. Es secuencial y final — ningún worktree.
- El merge de los worktrees a `feature/cv-data-consistency`: secuencial,
  en el orden Commit 2 → 3 → 4 → 5 (aunque los conjuntos son disjuntos,
  se integra en orden para que cada commit deje el repo verde de forma
  trazable).

## Cómo lanzar cada worktree

Dado que las 3 fases son chicas (Fase 1: 2 archivos; Fase 2: 5; Fase 3:
4-5), la paralelización es **opcional**. Para un plan Medium de este
tamaño, ejecución secuencial directa es razonable y más simple de
verificar. Si se decide paralelizar:

```bash
# desde feature/cv-data-consistency, tras el Commit 1
git worktree add ../portfolio-fase1 feature/cv-data-consistency
git worktree add ../portfolio-fase2 feature/cv-data-consistency
git worktree add ../portfolio-fase3 feature/cv-data-consistency
# cada agente trabaja su fase en su worktree, commitea, y se integran
# en orden a feature/cv-data-consistency
```

> Recomendación: por el tamaño chico, **ejecutar secuencial** (Commit 2 →
> 3 → 4 → 5 → 6 en la misma rama). Los worktrees agregan overhead de
> coordinación que no compensa para ~12 archivos. La tabla de
> colisiones queda documentada por si el plan crece.

[← Commits](05-commits.md) · [Verificación E2E →](07-verificacion-e2e.md)
