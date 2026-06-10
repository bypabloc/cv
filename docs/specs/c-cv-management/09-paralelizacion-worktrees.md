# 09 — Seccion 10: paralelizacion con git worktrees

> Base secuencial primero; luego hasta 3 frentes en paralelo (cap <=4
> agentes, 1 workflow — [orchestration.md](../../../.claude/rules/orchestration.md)).
> [Volver al README](README.md).

## Base secuencial (NO paralelizar)

Commits 1-4: plan + recursos declarativos + refactor `cv_write` +
scaffold `cv_admin`. Tocan archivos transversales (`shared/db`,
`seed_service`, catalogos de resources) y definen el CONTRATO (models
Pydantic / shapes) que el resto consume. Tambien la Fase 0 operativa
(branch Neon dev) es secuencial y manual.

## Fases worktree-safe (tras el commit 4)

| Worktree | Tareas | Archivos | Colisiones |
|----------|--------|----------|------------|
| `wt-backend` | T5 + T6 (content por entidad) | `services/cv_admin/core/**` | ninguna con los otros |
| `wt-devtools` | T7 (db_export + workflow) | `devtools/db_export/**`, `.github/workflows/db-backup.yml` | ninguna |
| `wt-admin` | T9 + T10 + T11 (feature UI) | `admin/**` | ninguna; consume el contrato congelado del commit 4-6 (tipos TS espejo) |

- 3 worktrees + el checkout principal = dentro del cap de sesiones/agentes.
- `isolation: 'worktree'` SOLO porque mutan archivos en paralelo.
- Cada worktree: `pnpm install` propio + copiar `.env` gitignored
  (`cp -rn docker/env/. .claude/worktrees/<X>/docker/env/`) ANTES de
  cualquier build/push ([parallel-sessions.md](../../../.claude/rules/parallel-sessions.md)).

## Lo que NO se paraleliza

- Commits 9-10 (seed S3 + eliminar `seeds/data`): dependen del snapshot
  verificado (gate 2.4) y tocan `services/db` que tambien toco el
  commit 3 — van en el checkout principal tras mergear `wt-devtools`.
- El deploy a dev (`cv_admin`, `db`) y la medicion de memoria.
- T12-T13 (E2E + verificacion final): SIEMPRE al final, un solo frente.

## Orden de merge

`wt-backend` → principal; luego `wt-devtools`; rebase de `wt-admin`
sobre el resultado (si los tipos del contrato cambiaron) → merge. Los
tres mergean a `feature/c-cv-management`, nunca directo a `dev`.
