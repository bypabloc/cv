# Seccion 10 — Paralelizacion con git worktrees

> Que se puede paralelizar y desde que commit. La cadena Fases A-D toca solo
> los `__init__.py` y pyproject.toml de subpaquetes shared DIFERENTES, asi
> que son worktree-safe. Fase E es 5 commits independientes (uno por service)
> tambien worktree-safe. Fase F y G son secuenciales.

## Base secuencial (NO se paraleliza)

Estos commits deben estar mergeados a `feature/shared-only-imports` ANTES
de lanzar worktrees:

| Commit | Por que es base |
|--------|-----------------|
| 1 (plan) | Crea la carpeta del plan; todos los worktrees la consultan |

Despues del commit 1, se puede ramificar.

## Fases worktree-safe (paralelo)

### Bloque 1 — Fases A-D (re-exports en shared)

Cada fase toca un subpaquete shared diferente. Pueden lanzarse en paralelo
desde el mismo SHA (commit 1):

| Worktree | Archivos exclusivos | Comando de creacion |
|----------|---------------------|---------------------|
| `worktree-fase-a-pydantic` | `shared/core/__init__.py`, `shared/core/pyproject.toml` + tests `shared/tests/unit/shared/core/test_pydantic_reexport.py` | `git worktree add ../portfolio-fase-a feature/shared-only-imports` |
| `worktree-fase-b-sqlalchemy` | `shared/db/__init__.py` + tests `shared/tests/unit/shared/db/test_sqlalchemy_reexport.py` | `git worktree add ../portfolio-fase-b feature/shared-only-imports` |
| `worktree-fase-c-aws` | `shared/aws/ses.py`, `shared/aws/dynamodb_types.py` (nuevo), `shared/aws/__init__.py` + 4 tests en `shared/tests/unit/shared/aws/` | `git worktree add ../portfolio-fase-c feature/shared-only-imports` |
| `worktree-fase-d-observability` | `shared/observability/__init__.py` + test `shared/tests/unit/shared/observability/test_metric_unit_reexport.py` | `git worktree add ../portfolio-fase-d feature/shared-only-imports` |

Cero solapamiento de archivos. Cada worktree termina con un commit
atomico que se mergea de vuelta a `feature/shared-only-imports` (fast-forward
o `git merge --no-ff` segun preferencia; el orden no importa).

### Bloque 2 — Fase E (migracion services)

ARRANCA cuando los commits 2-5 (Fases A-D) estan en
`feature/shared-only-imports`. Cada service toca archivos exclusivos:

| Worktree | Archivos exclusivos |
|----------|---------------------|
| `worktree-cv` | `services/cv/core/**` solamente |
| `worktree-db` | `services/db/core/**` solamente |
| `worktree-contact-form` | `services/contact_form/core/**` + `services/contact_form/pyproject.toml` |
| `worktree-tracking-pixel` | `services/tracking_pixel/core/**` |
| `worktree-stream-processor` | `services/stream_processor/core/**` |

Cero solapamiento. Cada worktree corre `serverless tests --type=unit
--lambda=<X>` antes de commit. Re-merge a `feature/shared-only-imports`
sin conflictos.

## Lo que NO se paraleliza

| Fase | Razon |
|------|-------|
| Commit 1 (plan) | Es la base de todos los worktrees |
| Fase F (lint-deps imports) | Edita `devtools/serverless/dep_validator.py` + crea `import_validator.py`. Conceptualmente independiente de los services, pero DEBE correr DESPUES de Fase E para que su check pase. Si se lanza en paralelo con E, el check fallaria sobre los commits intermedios y no podriamos mergear |
| Fase G (.claude/) | Edita 5+ archivos en `.claude/` y `CLAUDE.md`. Mejor secuencial, va al final, cuando el contrato esta estabilizado |
| Verificacion E2E (commit 13) | Es la fase de cierre: corre la bateria completa, elimina la carpeta del plan. NO se paraleliza |

## Orden recomendado de lanzamiento

```text
T0:  commit 1 (plan) -> push a feature/shared-only-imports
T1:  4 worktrees en paralelo (fases A, B, C, D)
T2:  merge de los 4 worktrees a feature/shared-only-imports
     -> commits 2, 3, 4, 5 (orden cualquiera)
T3:  5 worktrees en paralelo (fase E: cv, db, contact_form, tracking_pixel, stream_processor)
T4:  merge de los 5 worktrees -> commits 6, 7, 8, 9, 10
T5:  commit 11 (Fase F: lint-deps imports)
T6:  commit 12 (Fase G: rule + skill + docs)
T7:  commit 13 (verificacion E2E + git rm del plan)
T8:  git push + crear PR (gate de cierre del plan-format)
```

Limite: maximo 5 agentes concurrentes (lo permite la regla del plan-format).

## Anti-patrones

- Lanzar Fase F antes de Fase E completa: el check de imports falla y bloquea
  los worktrees.
- Lanzar dos worktrees que toquen el mismo `__init__.py` (no aplica aqui,
  pero recordatorio general).
- Mergear un worktree sin correr `lint-deps` + `tests` previamente.
- Saltarse el merge incremental: cada worktree debe re-mergear a
  `feature/shared-only-imports` ANTES de lanzar el siguiente bloque.

## Limpieza

```bash
git worktree list
git worktree remove ../portfolio-fase-a
# ...etc
git worktree prune
```
