# Paralelizacion con git worktrees

## Base secuencial obligatoria (NO se paraleliza)

Los siguientes commits TODOS los worktrees necesitan, asi que deben estar
en la rama base ANTES de lanzar worktrees:

- **Commit 1**: `docs(specs): plan contact-form-latency-optim` — todos los
  worktrees necesitan poder consultar el plan.

Tras commit 1, la rama `feature/contact-form-latency-optim` esta lista
para fan-out.

## 2 Worktrees

### Worktree A — `shared/` (kit independiente)

**Branch**: `feature/contact-form-latency-optim-shared`.
**Path**: `../portfolio-worktree-shared/`.
**Scope**: lo que vive en `shared/lambda_kit/` y `shared/rate_limit/`.

Commits que avanza:
- Commit 2 (test snap_start_warmup Red).
- Commit 3 (snap_start_warmup Green).
- Commit 4 (test check_or_raise paralelo Red).
- Commit 5 (refactor check_or_raise paralelo Green).

Archivos exclusivos:

```
serverless/lambda/shared/lambda_kit/snap_start_warmup.py          (NUEVO)
serverless/lambda/shared/lambda_kit/__init__.py                    (re-export)
serverless/lambda/shared/rate_limit/check.py                       (refactor)
serverless/lambda/shared/tests/unit/shared/lambda_kit/test_snap_start_warmup.py  (NUEVO)
serverless/lambda/shared/tests/unit/shared/rate_limit/test_check_parallel.py     (NUEVO)
```

NO toca `services/`. NO toca `manifest.yaml` de ningun lambda.

### Worktree B — `contact_form/` (consumer)

**Branch**: `feature/contact-form-latency-optim-wire`.
**Path**: `../portfolio-worktree-wire/`.
**Scope**: solo `services/contact_form/`.

Commits que avanza:
- Commit 6 (test wired warmup Red).
- Commit 7 (handler.py + manifest.yaml Green).

Archivos exclusivos:

```
serverless/lambda/services/contact_form/core/handler.py
serverless/lambda/services/contact_form/manifest.yaml
serverless/lambda/services/contact_form/tests/unit/test_handler_warmup_wired.py  (NUEVO)
```

**DEPENDENCIA CRITICA**: el commit 6 (Red) y el commit 7 (Green) del worktree B
**DEPENDEN** del commit 3 (`snap_start_warmup` Green) del worktree A — el handler
importa `from shared.lambda_kit.snap_start_warmup import register_warmup`. Si
ese modulo no existe aun, los tests del worktree B fallan con `ModuleNotFoundError`.

Por eso el worktree B **espera el commit 3 mergeado a la rama base** antes
de empezar. NO se lanza en T0 con el worktree A.

## Tabla de colision de archivos

| Archivo | Worktree A | Worktree B |
|---------|------------|------------|
| `shared/lambda_kit/snap_start_warmup.py` | NUEVO | importa |
| `shared/lambda_kit/__init__.py` | modifica | importa |
| `shared/rate_limit/check.py` | refactor | importa transitivo |
| `shared/tests/.../test_snap_start_warmup.py` | NUEVO | — |
| `shared/tests/.../test_check_parallel.py` | NUEVO | — |
| `services/contact_form/core/handler.py` | — | modifica |
| `services/contact_form/manifest.yaml` | — | modifica |
| `services/contact_form/tests/.../test_handler_warmup_wired.py` | — | NUEVO |
| `docs/specs/contact-form-latency-optim/` | — (ya en base) | — (ya en base) |

**File exclusivity: OK**. Ningun archivo se toca en ambos worktrees al mismo tiempo.

## Secuencia de ejecucion

```
T0 (rama base): commit 1 (docs plan)
  |
  v
T1 (worktree A se lanza):
  - commit 2 (test snap_start_warmup Red)
  - commit 3 (snap_start_warmup Green)
  - commit 4 (test check paralelo Red)
  - commit 5 (refactor check paralelo Green)
  - merge worktree A -> rama base
  |
  v
T2 (worktree B se lanza, requiere commit 3 ya en base):
  - commit 6 (test wired warmup Red)
  - commit 7 (handler.py + manifest.yaml Green)
  - merge worktree B -> rama base
  |
  v
T3 (en rama base, secuencial):
  - commit 8 (coverage + integration verdes)
  - commit 9 (baseline metrics)
  - deploy a dev + smoke + tabla metrics
  - commit 10 (cierra plan + git rm)
  |
  v
T4: PR feature/contact-form-latency-optim -> dev (un solo PR atomico)
```

## Lo que NO se paraleliza

- **Commit 1**: plan, base de todos.
- **Commits 8, 9, 10**: dependen del estado completo del codigo + de los
  smokes deployados. Son secuenciales en la rama base.
- **Deploy + smoke en los 3 envs**: son secuenciales por env
  (dev -> stage -> main) por el flujo enforced del proyecto.

## Como lanzar cada worktree

```bash
# Desde la raiz del repo, en la rama base feature/contact-form-latency-optim
# con commit 1 ya commiteado:

# Worktree A
git worktree add -b feature/contact-form-latency-optim-shared \
  ../portfolio-worktree-shared feature/contact-form-latency-optim

# Worktree B (lanzar SOLO despues de mergear commit 3 a la rama base)
git worktree add -b feature/contact-form-latency-optim-wire \
  ../portfolio-worktree-wire feature/contact-form-latency-optim
```

## Merge de worktrees a la base

```bash
# Worktree A -> rama base
cd /home/bypabloc/projects/bypabloc/portfolio
git checkout feature/contact-form-latency-optim
git merge --no-ff feature/contact-form-latency-optim-shared
git worktree remove ../portfolio-worktree-shared

# Tras eso, lanzar worktree B (necesita commit 3 que ahora esta en base).
# Despues:
git merge --no-ff feature/contact-form-latency-optim-wire
git worktree remove ../portfolio-worktree-wire
```
