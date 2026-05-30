# 09 — Sección 10: paralelización con git worktrees

[← 08 commits](08-commits.md) · [Siguiente: Sección 11 →](10-verificacion-e2e.md)

> Caps: <=4 agentes concurrentes, 1 workflow a la vez
> ([orchestration.md](../../../.claude/rules/orchestration.md)).

## Base secuencial (NO paralelizar)

Commits 1–4: la carpeta del plan + `shared.crypto` (token + orquestador) +
limpieza de `shared.http` + transporte. Todo el resto importa de
`shared.crypto` y depende del rename del header/`_meta` → deben existir y estar
verdes ANTES de abrir worktrees. Son archivos transversales (`shared/**`).

## Ola worktree-safe (opcional)

Tras el commit 4, una sola ola de <=4 worktrees, archivos disjuntos:

| Worktree | Tarea | Archivos |
|----------|-------|----------|
| wt-contact | T6 | `services/contact_form/**` |
| wt-auth | T7 | `services/auth/**` |
| wt-tracking | T8 | `services/tracking_pixel/**` |
| wt-cv | T9 | `services/cv/**` |

`isolation: 'worktree'` SOLO acá. En esta ejecución se hace inline secuencial
(el costo de coordinación supera el ahorro para 4 cambios chicos).

## NO se paraleliza

Base secuencial, devtools (T10/T11), secrets (T12), docs (T13), y la
verificación E2E (sección 11). El review adversarial final SÍ usa workflow
(lectura pura, sin conflicto de archivos).

[← 08 commits](08-commits.md) · [Siguiente: Sección 11 →](10-verificacion-e2e.md)
