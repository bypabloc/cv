# 10 — Paralelizacion con git worktrees

[< 09 Commits](09-commits.md) | [Siguiente: 11 Verificacion E2E >](11-verificacion-e2e.md)

## Base secuencial (no paralelizable)

Estos commits los necesitan TODOS los worktrees o tocan archivos
transversales — van ANTES de abrir cualquier worktree, en la branch
principal:

| Commit | Por que es base |
|--------|-----------------|
| C-1 (plan) | la carpeta del plan |
| C-2 (auditoria) | T-1 cierra las listas que TODAS las fases consumen |
| C-3 (shared/db) | C-5 y C-6 importan de `shared.db` |
| C-4 (shared/lambda_kit) | C-5..C-8 importan de `shared.lambda_kit` |

Sin C-3 y C-4 mergeados, los worktrees de los Lambdas no compilan.

## Fases worktree-safe (archivos disjuntos)

Tras C-4, se pueden abrir worktrees concurrentes:

| Worktree | Commit | Archivos (disjuntos) |
|----------|--------|----------------------|
| W-db | C-5 | `serverless/lambda/services/db/core/**` |
| W-stream | C-6 | `serverless/lambda/services/stream_processor/core/**` |
| W-contact | C-7 | `serverless/lambda/services/contact_form/core/**` |
| W-tracking | C-8 | `serverless/lambda/services/tracking_pixel/core/**` |
| W-venv | C-9 | `devtools/serverless/venv.py` + sus tests |

5 worktrees concurrentes — dentro del limite 5-7. Cada uno toca un
arbol de archivos exclusivo: cero colision.

> C-9 (venv) toca SOLO `venv.py` nuevo + tests nuevos. NO toca
> `local_runtime.py` ni `lambda_controller.py` — ese cambio es C-10,
> que NO es worktree-safe.

## Lo que NO se paraleliza

Tras mergear las 5 fases worktree-safe, el resto es secuencial en la
branch principal:

| Commit | Por que NO es worktree-safe |
|--------|-----------------------------|
| C-10 | toca `serverless/pyproject.toml` (config central) + `local_runtime.py` + `lambda_controller.py` (modulos compartidos de devtools) |
| C-11 | toca los 12 `pyproject.toml` + `quality.py` |
| C-12 y C-13 | AMBOS tocan `devtools/serverless/packaging.py` |
| C-14 | docs + rules — fase de cierre |
| C-15 | verificacion E2E — siempre el ultimo |

### Colision C-12 / C-13 en `packaging.py`

T-11 (validador dedup) y T-12 (peso) ambos modifican
`packaging.py`. NO se paralelizan: se hacen **secuenciales** (C-12
luego C-13). C-13 parte del repo con C-12 ya mergeado, asi el cambio en
`packaging.py` se apila sin conflicto.

## Como lanzar cada worktree

```bash
# Tras mergear C-1..C-4 en feature/serverless-lambda-independence:
git worktree add ../wt-db    feature/serverless-lambda-independence
git worktree add ../wt-stream feature/serverless-lambda-independence
# ... uno por fase worktree-safe.
# Cada worktree:
#   1. crea su sub-branch o commitea directo segun el flujo del equipo
#   2. corre su verificacion incremental (ver doc 09)
#   3. al terminar: merge a feature/serverless-lambda-independence
# git worktree remove ../wt-db   (al cerrar)
```

Cada worktree corre su `serverless tests --type=coverage --lambda=<x>`
con SU `.venv` aislado — los venvs no colisionan (cada Lambda el suyo).

## Tabla de colisiones (resumen)

| Archivo | Commits que lo tocan | Estrategia |
|---------|----------------------|------------|
| `serverless/lambda/shared/db/**` | C-3 | base secuencial |
| `serverless/lambda/shared/lambda_kit/**` | C-4 | base secuencial |
| `services/db/core/**` | C-5 | W-db exclusivo |
| `services/stream_processor/core/**` | C-6 | W-stream exclusivo |
| `services/contact_form/core/**` | C-7 | W-contact exclusivo |
| `services/tracking_pixel/core/**` | C-8 | W-tracking exclusivo |
| `devtools/serverless/venv.py` | C-9 | W-venv exclusivo |
| `serverless/pyproject.toml` | C-10, C-11 | secuencial |
| `devtools/serverless/packaging.py` | C-12, C-13 | secuencial |
| `devtools/serverless/lambda_controller.py` | C-10, C-13 | secuencial |

[< 09 Commits](09-commits.md) | [Siguiente: 11 Verificacion E2E >](11-verificacion-e2e.md)
