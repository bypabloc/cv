# 12 — Paralelización con git worktrees

[← 11 commits](11-commits.md) · [siguiente: 13 verificación →](13-verificacion-e2e.md)

> Desde qué commit se puede paralelizar con git worktrees y qué fases son
> worktree-safe (archivos disjuntos). `isolation: 'worktree'` SÓLO cuando los
> agentes mutan archivos en paralelo. Cap: **≤4 agentes**, **1 workflow**.

## Base secuencial (antes de cualquier worktree)

Deben estar commiteados en la rama base del plan ANTES de lanzar worktrees:

- T0 (carpeta plan), **T1 (Fase 0 — gate bloqueante)**, T2+T3 (shared
  foundations), T4+T5+T6 (devtools).
- Razón: `send_email`, los encoders, cv y los callers DEPENDEN de
  `shared.aws.lambda_invoke`, `shared.templating`, del `after_restore` hook (T1)
  y del provisioner con `uses.invokes`/`uses.buckets`. Lanzar worktrees antes =
  conflictos. **T1 es gate absoluto**: nada empieza sin el baseline de cold.

## Olas worktree-safe

| Ola | Tareas | Worktrees | Por qué seguro |
|-----|--------|-----------|----------------|
| B | T7 (+T7b) | 1 (`send_email`) | dir nuevo `services/send_email/` |
| C | T8, T9, T10, T11 | hasta 4 | un lambda/dir cada uno (contact_form, tracking_pixel, tracking_writer, cv) |
| D | T12, T13 | 2 | auth, users (dirs distintos) |

## Lo que NO se paraleliza

- T1 (Fase 0) — gate bloqueante, secuencial, primero de todo.
- T6 (quitar SQS de devtools) — toca el provisioner que todos usan.
- T14 (borrar colas/workers) — depende de que los callers ya no usen la cola.
- T15/T16 (stream_processor + rules) — T16 toca CLAUDE.md + rules transversales.
- T17 (verificación E2E + gate de cold) — secuencial, gate final.

## Cómo lanzar un worktree

```bash
git worktree add ../portfolio-send-email feature/serverless-sqs-send-email
```

[← 11 commits](11-commits.md) · [siguiente: 13 verificación →](13-verificacion-e2e.md)
