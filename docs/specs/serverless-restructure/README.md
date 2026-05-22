# Reestructuracion del backend serverless + CLI

> Plan de implementacion del refactor del backend serverless del
> portfolio: nueva estructura de carpetas, CLI unificado y recursos
> compartidos como stacks independientes. El commit 1 ya esta hecho;
> este documento cubre los commits 2 a 5.

## Estado

| Commit | Descripcion | Estado |
|--------|-------------|--------|
| 1 | Estructura `serverless/lambda/` + paths devtools | HECHO (`5b510f5`) |
| 2 | CLI: unificar `tests` y `run` | Pendiente |
| 3 | Recursos como stack-por-recurso + SSM | Pendiente |
| 4 | Eliminar `db-*` + extender la Lambda `db` | Pendiente |
| 5 | Docs + rules + skill + CLAUDE.md | Pendiente |

Rama: `feature/serverless-restructure` (commit 1 ya commiteado ahi).

## Navegacion

| Documento | Cuando leer |
|-----------|-------------|
| [01-commit-2-cli-tests-run.md](01-commit-2-cli-tests-run.md) | Unificar `test-*` en `tests --type` y `run-local`/`invoke-remote` en `run` |
| [02-commit-3-resources.md](02-commit-3-resources.md) | Recursos compartidos como stacks independientes + SSM |
| [03-commit-4-drop-db.md](03-commit-4-drop-db.md) | Eliminar comandos `db-*` + controllers `seed`/`tables` en la Lambda `db` |
| [04-commit-5-docs.md](04-commit-5-docs.md) | Actualizar rules, docs y skill |
| [05-paralelizacion-worktrees.md](05-paralelizacion-worktrees.md) | Que commits se pueden hacer en paralelo con git worktrees |

## Contexto

El backend serverless tenia tres problemas de organizacion (detalle en
la conversacion que origino este plan):

1. **CLI inconsistente**: `test-unit`/`test-integration` separados,
   `run-local`/`invoke-remote` como verbos distintos, 8 comandos `db-*`
   que son wrappers de `aws lambda invoke`.
2. **Carpetas sueltas**: `tests/` colgaba de la raiz; `src/` y `shared/`
   no comunicaban pertenencia al mismo dominio.
3. **Infra monolitica**: `infra.yaml` definia todo en un stack; los
   lambdas no declaraban que recursos consumen.

El commit 1 resolvio (2) y dejo la base para (1) y (3).

## Decisiones tomadas (no reabrir)

- Layout: `serverless/lambda/{services,shared,resources}/`.
- `shared/` se movio sin nivel `src/` interno (la carpeta ES el paquete
  importable).
- CLI tests: `tests --type=unit|integration|coverage`, target
  `--lambda=<nombre>` o `--shared[=<subpaquete>]`, sin target = todo.
- CLI run: `run --stage=local|dev|stage|prod`. `local` -> `sam local
  invoke`; resto -> `aws lambda invoke`.
- `coverage` es un tercer `--type`, NO un flag ortogonal.
- Recursos: stack-por-recurso, cada uno publica a SSM (no `Export` /
  `Fn::ImportValue`). `lambda.yaml` declara `resources:` por nombre.
- Los 8 `db-*` se eliminan; migrate/seed/tables/etc. se hacen con
  `run --lambda=db`. La Lambda `db` se extiende con controllers `seed`
  y `tables` (hoy solo tiene migrate/downgrade/current/show-migrations/
  stamp).
- `db-shell` y `db-branch` (psql / neonctl, no invocan lambda) se
  eliminan sin reemplazo en el CLI; se usan a mano.

## Reglas criticas

- SIEMPRE verificar Python de devtools con `devtools/.venv/bin/python`
  (3.14), nunca `python3` del shell.
- El commit 3 toca infra de produccion: verificar con `cfn-lint` /
  `sam validate`; el deploy real lo hace el usuario en `dev` antes de
  promover.
- NUNCA atribucion de IA en commits.
- Conventional Commits en espanol.
