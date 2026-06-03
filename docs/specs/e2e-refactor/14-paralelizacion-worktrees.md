# 14 — Seccion 10: Paralelizacion con git worktrees

[<- 13 commits](13-commits.md) | [Siguiente: 15 verificacion e2e ->](15-verificacion-e2e.md)

> Desde que commit se puede paralelizar y que fases son worktree-safe. CAPS:
> **<=4 agentes concurrentes**, **1 workflow a la vez** (orchestration.md).

## Base secuencial (NO se paraleliza)

Los commits 1-4 tocan archivos transversales que todos los modulos importan:

- Commit 1 (plan), 2 (deps pyproject), 3 (`tests/shared/`), 4 (`devtools/e2e/`
  + container).

`tests/shared/` y `devtools/e2e/` son la interfaz que C/D/E consumen: deben
estar ESTABLES y commiteados antes de lanzar worktrees. Lanzar un worktree
antes de commitear `tests/shared` -> los 3 worktrees pelean por el mismo
archivo base.

## Ola worktree-safe (commits 5, 6, 7)

Tras commitear la base (1-4), los 3 modulos tocan carpetas DISJUNTAS:

| Worktree | Fase | Archivos (disjuntos) | Commit |
|----------|------|----------------------|--------|
| wt-api | C | `tests/api/*` | 5 |
| wt-admin | D | `tests/admin/*` | 6 |
| wt-app | E | `tests/app/*` | 7 |

Cero colision: cada uno escribe solo su carpeta + su `conftest.py` local.
Todos LEEN `tests/shared/` (read-only, ya commiteado). El `tests/conftest.py`
raiz y `tests/pyproject.toml` ya estan commiteados (base) — NO se tocan en la
ola.

`isolation: 'worktree'` SOLO aqui (mutan archivos en paralelo). Cap: 3
agentes (<=4). Cada worktree corre su `pytest tests/<module>` via Bash (no 1
agente por test).

### Lanzar la ola

```text
git commit (base 1-4) en feature/e2e-refactor
-> 3 worktrees desde feature/e2e-refactor:
     wt-api   -> implementa tests/api/   -> commit 5
     wt-admin -> implementa tests/admin/ -> commit 6
     wt-app   -> implementa tests/app/   -> commit 7
-> merge de los 3 worktrees a feature/e2e-refactor (sin conflicto: disjuntos)
```

## Lo que NO se paraleliza

- **Commit 8 (eliminacion)**: toca config TRANSVERSAL (hook, CI, compose,
  CLAUDE.md, flags de test_runner, refs en multiples paquetes). Secuencial,
  DESPUES de mergear los 3 worktrees.
- **Commit 9 (rule+skill)**: el `claude -p` de validacion cambia la cuenta
  gh activa (gotcha de memory). Secuencial, no en paralelo con git ops.
- **Commit 10 (verificacion seccion 11)**: gate final, secuencial.
- La grilla de comandos de verificacion (seccion 11) y la limpieza
  (`git rm -r docs/specs/`): NO se paralelizan.

## Anti-patrones evitados

- NO lanzar worktrees antes de commitear `tests/shared` + `devtools/e2e`
  (conflicto garantizado en la interfaz compartida).
- NO `isolation: 'worktree'` para tareas read-only (la verificacion corre en
  Bash, no en worktrees).
- NO >4 worktrees concurrentes (rate-limit).

[<- 13 commits](13-commits.md) | [Siguiente: 15 verificacion e2e ->](15-verificacion-e2e.md)
