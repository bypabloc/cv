# 11 — Paralelizacion con git worktrees

[README](README.md) | [10-commits](10-commits.md) |
**11-paralelizacion-worktrees** | [12-verificacion-e2e](12-verificacion-e2e.md)

## Base secuencial (NO worktree-safe)

Los commits 1-5 tocan archivos transversales / config central / shared/db
y deben ejecutarse **secuenciales** en la rama principal del feature.
Ningun worktree puede empezar antes de que estos commits esten:

| Commit | Por que es base secuencial |
|---|---|
| 1 | Crea la carpeta del plan + diagrama; cualquier worktree leera de aqui |
| 2 | Refactoriza shared/db/models/ (todos los lambdas dependen) |
| 3 | Cambia `__tablename__` en los modelos (referencia comun) |
| 4 | Crea la migracion Alembic (artefacto unico, no paralelizable) |
| 5 | Refactoriza seed_service (todos los lambdas leen seeds) |

Total: ~5 commits secuenciales en `feature/group-tables-by-domain`.

## Fases worktree-safe (despues del commit 5)

A partir del commit 5 mergeado, los lambdas downstream pueden trabajarse
en paralelo porque tocan archivos disjuntos.

### Tabla de fases paralelas

| Worktree | Branch | Archivos | AC | Verify |
|---|---|---|---|---|
| WT-A | `feature/group-tables-by-domain` + commit 6 | `services/db/core/controllers/*`, `services/db/core/services/*`, `shared/db/cv_repository.py`, `shared/db/repository.py` | AC-8 (db) | `serverless tests --type=unit --lambda=db && serverless tests --type=integration --lambda=db` |
| WT-B | branch worktree desde commit 5 -> rebase | `services/stream_processor/core/services/*`, sus tests | AC-3 | `serverless tests --type=integration --lambda=stream_processor` + verificacion DB real |
| WT-C | branch worktree desde commit 5 -> rebase | `services/contact_form/core/services/*`, sus tests | AC-5 | `serverless tests --type=integration --lambda=contact_form` + verificacion DB real |
| WT-D | branch worktree desde commit 5 -> rebase | `services/tracking_pixel/core/services/*`, sus tests | AC-3 | `serverless tests --type=integration --lambda=tracking_pixel` + verificacion DB real |
| WT-E (opcional) | branch worktree desde commit 5 -> rebase | `services/cv/core/*` (si existe) | AC del cv | `serverless tests --type=integration --lambda=cv` |

### File Exclusivity check

- Cada lambda vive en `services/<lambda>/` — files disjuntos
- Tests viven en `services/<lambda>/tests/` — disjuntos
- Ningun worktree toca `shared/`, `manifest.yaml`, `pyproject.toml` raiz,
  workflows CI, ni `_init_schema_extras.py`

PASA: 4-5 worktrees pueden correr concurrentes sin conflictos.

### Interface Stability check

Los modelos en `shared/db/models/` quedaron estables en el commit 3
(con sus `__tablename__` nuevos). El seeder quedo estable en commit 5.
Los lambdas solo CONSUMEN estas interfaces (no las modifican). PASA.

### Bounded Scope check

Cada worktree es 1-3 archivos del lambda + sus tests integration. Tamano
acotado (~5 archivos por worktree). PASA.

## Comandos para lanzar worktrees

```bash
# Despues del commit 5 commiteado en feature/group-tables-by-domain

# Worktree para stream_processor
git worktree add ../worktree-stream-processor feature/group-tables-by-domain
cd ../worktree-stream-processor
git checkout -b worktree/stream-processor

# Worktree para contact_form (en paralelo, en otro shell)
git worktree add ../worktree-contact-form feature/group-tables-by-domain
cd ../worktree-contact-form
git checkout -b worktree/contact-form

# Worktree para tracking_pixel
git worktree add ../worktree-tracking-pixel feature/group-tables-by-domain
cd ../worktree-tracking-pixel
git checkout -b worktree/tracking-pixel

# Worktree para db (controllers + repositorios)
git worktree add ../worktree-db feature/group-tables-by-domain
cd ../worktree-db
git checkout -b worktree/db
```

Cada worktree:
1. Implementa los cambios del lambda asignado
2. Corre sus tests (unit + integration con verificacion DB real)
3. Commitea localmente
4. Hace `git push -u origin worktree/<X>` (rama propia, NO mergea aun)
5. Notifica al orquestador "done"

## Re-integracion al feature branch principal

Despues de que TODOS los worktrees terminen:

```bash
cd <repo principal>
git checkout feature/group-tables-by-domain

# Merge cada worktree de vuelta (en orden, NO en paralelo)
git merge worktree/db --no-ff -m "merge: db lambda actualizado"
# correr verificacion del feature/main
serverless tests --type=integration --lambda=db

git merge worktree/stream-processor --no-ff
serverless tests --type=integration --lambda=stream_processor

git merge worktree/contact-form --no-ff
serverless tests --type=integration --lambda=contact_form

git merge worktree/tracking-pixel --no-ff
serverless tests --type=integration --lambda=tracking_pixel

# Limpiar worktrees
git worktree remove ../worktree-db
git worktree remove ../worktree-stream-processor
git worktree remove ../worktree-contact-form
git worktree remove ../worktree-tracking-pixel
```

## Lo que NO se paraleliza

- **Commits 1-5**: ya cubierto arriba
- **Commit 11** (tests integration del shared kit): toca fixtures
  compartidas
- **Commit 12** (bateria E2E + cleanup): es la verificacion final del
  feature, requiere todo lo demas ya mergeado
- **Fase 5** (provision stage/prod): es operativo post-merge, no es
  desarrollo paralelo

## Conflictos esperados al re-mergear

- `pyproject.toml` raiz si algun worktree agrego dep (raro — los
  lambdas tienen su propio `pyproject.toml` con dep aislado)
- Tests integration: cada worktree agrega fixtures en su lambda,
  ningun conflicto esperado en `_fixtures/` compartido
- En general: cero conflictos esperados por File Exclusivity check

## Limite de worktrees

Maximo **5 worktrees concurrentes** (incluye el repo principal). Mas
satura RAM con docker stacks + python venvs activos. En la practica
recomendado 3-4.

## Cuando NO usar worktrees

Si el desarrollador prefiere ejecucion lineal (un commit a la vez en
el feature branch principal), es perfectamente valido. Los worktrees
son una OPTIMIZACION cuando hay tiempo paralelo + bandwidth mental
para mantener 4 contextos. La spec NO requiere worktrees — los commits
6-9 (uno por lambda) pueden correr secuenciales en `feature/group-tables-by-domain`
sin problemas.
