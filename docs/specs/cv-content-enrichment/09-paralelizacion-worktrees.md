# Sección 10 — Paralelización con git worktrees

[← Commits](08-commits.md) · [Verificación E2E →](10-verificacion-e2e.md)

## Base secuencial

El **Commit 1** (carpeta del plan) y el **Commit 2** (schema Zod
`country` + `metricsEstimated`) son la base secuencial: las fases de
contenido dependen de que los campos del schema existan. Todo worktree
parte del Commit 2.

## Tabla de fases worktree-safe

Tras el Commit 2, estas fases tocan archivos disjuntos y pueden ir en
paralelo:

| Fase / Commit | Archivos | Colisión |
|---------------|----------|----------|
| Commit 3 (Fase 2 — DB) | `serverless/lambda/shared/db/models/*.py`, migración Alembic, `db/cv/seed/seed_from_yaml.py` | Ninguna — backend Python, aislado del frontend |
| Commit 4 (Fase 3 — experiencias) | `packages/content/src/data/experiences/*.yaml`, baseline | Ninguna |
| Commit 5 (Fase 4 — proyectos) | `packages/content/src/data/projects/*.yaml`, baseline | Ninguna |
| Commit 6 (Fase 5 — summary) | `packages/content/src/data/i18n/curriculum/*.yaml` | Ninguna |

Análisis de los 3 checks:

- **File Exclusivity**: los 4 conjuntos son disjuntos. Commits 4, 5 y 6
  tocan subcarpetas distintas de `packages/content/src/data/`
  (`experiences/`, `projects/`, `i18n/curriculum/`). El Commit 3 es
  backend Python — no comparte ningún archivo con el frontend.
- **Interface Stability**: el Commit 2 fija el schema; las fases 3-5 solo
  agregan data conforme a ese schema. El Commit 3 no cambia ninguna
  interfaz que el frontend consuma.
- **Bounded Scope**: cada fase tiene su Definition of Done acotada.

Riesgo compartido: el `data-parity` baseline. Los Commits 4 y 5 lo
actualizan (`experiences.json` y `projects.json` — archivos distintos
dentro de `tests/fixtures/baseline/`, sin colisión real).

## Lo que NO se paraleliza

- **Commits 1 y 2** (base secuencial): antes de lanzar worktrees.
- **Commit 7** (componentes de detalle en `app-shared`): depende de que
  la data de las fases 3-5 esté integrada (los componentes renderizan
  esa data).
- **Commit 8** (rutas en las 6 apps): depende del Commit 7.
- **Commit 9 / Fase 7** (verificación E2E): secuencial y final.

## Cómo lanzar cada worktree

Tras el Commit 2, los Commits 3, 4, 5, 6 se pueden trabajar en paralelo:

```bash
git worktree add ../portfolio-db feature/cv-content-enrichment      # Commit 3
git worktree add ../portfolio-exp feature/cv-content-enrichment     # Commit 4
git worktree add ../portfolio-proj feature/cv-content-enrichment    # Commit 5
git worktree add ../portfolio-summ feature/cv-content-enrichment    # Commit 6
```

Cada worktree integra su commit a `feature/cv-content-enrichment` en el
orden 3 → 4 → 5 → 6. Luego, secuencial: Commit 7 → 8 → 9.

> El Commit 3 (DB) es el mejor candidato a paralelizar: es backend
> Python, lo trabaja un agente distinto sin tocar nada del frontend. Los
> Commits 4-6 son data YAML — útil paralelizarlos solo si el contenido
> de cada uno es voluminoso. Por el volumen de contenido a redactar
> (9 experiencias + 7 proyectos + 5 summaries), paralelizar 3/4/5/6
> tiene sentido en este plan.

[← Commits](08-commits.md) · [Verificación E2E →](10-verificacion-e2e.md)
