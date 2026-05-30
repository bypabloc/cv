# 10 — Paralelización con git worktrees

[← 09 commits](09-commits.md) · [siguiente: 11 verificación E2E →](11-verificacion-e2e.md)

> Qué se paraleliza con worktrees / subagentes y qué no. Gobernado por
> [orchestration.md](../../../.claude/rules/orchestration.md): **≤4 agentes
> concurrentes**, **1 workflow a la vez**, Opus 4.8. `isolation:'worktree'`
> SÓLO cuando los agentes mutan archivos en paralelo.

## Base secuencial (commits 1-8) — NO worktree

- Commit 1 (carpeta del plan).
- Commits 2-3 (shared T1, T2): archivos disjuntos (`lambda_invoke.py` vs
  `templating/`) → 2 agentes o inline.
- Commits 4-6 (devtools T3, T4, T5): T3 (`provisioner.py`) y T4
  (`infra_provision.py`) en 2 agentes concurrentes; **T5 NO** (re-toca ambos
  → secuencial tras T3/T4).
- Commits 7-8 (`send_email` T6 + seed T6b): un solo dir nuevo → 1 agente o
  worktree único. Habilita a los callers (T7, T9, T10).

> No se lanza ninguna ola worktree hasta tener la base (commits 1-8)
> commiteada: `shared.aws.lambda_invoke` y `send_email` son dependencias de
> los callers.

## Ola worktree A — Encoders + auth/users (tras la base)

| Worktree | Tarea | Archivos (disjuntos) |
|----------|-------|----------------------|
| wt-contact | T7 | `services/contact_form/**` |
| wt-tracking | T8 | `services/tracking_pixel/**` |
| wt-auth | T9 | `services/auth/**` |
| wt-users | T10 | `services/users/**` |

4 agentes concurrentes (cap exacto), `isolation:'worktree'`. Cada lambda es un
dir disjunto → cero colisión. Todos dependen de T6 (`send_email`) ya commiteado
en la base, NO entre sí. Cada agente corre sus tests + lint-deps antes de su
commit.

## NO se paraleliza

- **T5** (quitar SQS de devtools): toca varios módulos compartidos → secuencial.
- **T11** (borrar workers + `shared.queue` + `resources/sqs/`): los 4 callers
  referencian `shared.queue` en su pyproject → DESPUÉS de Ola A, secuencial.
  Borrar `shared/queue/` antes rompería los imports.
- **T12/T13** (cleanup stream_processor + rules): tocan CLAUDE.md, rules,
  devtools, docs transversales → 2 agentes (archivos distintos) pero NO
  worktree (cambios de docs/config, mejor en el árbol principal con review).
- **T14** (verificación E2E): SIEMPRE secuencial, árbol principal, al final.
  La batería de la sección 11 NO se fan-outea.

## Lanzamiento y merge

- La Ola A se orquesta con UN workflow (1 a la vez) en una ola de 4, o con 4
  subagentes `isolation:'worktree'`. Modelo: Opus 4.8.
- Cada worktree commitea en su rama temporal; al cerrar, se integra a
  `feature/serverless-sqs-to-async-invoke`. Tras integrar la Ola A, se corre
  T11 (borrado) en el árbol principal.
- Las suites de verificación las corre cada agente en su worktree con Bash —
  NO un agente por suite.

[← 09 commits](09-commits.md) · [siguiente: 11 verificación E2E →](11-verificacion-e2e.md)
