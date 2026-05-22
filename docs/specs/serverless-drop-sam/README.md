# Eliminacion de SAM — backend serverless gestionado con AWS CLI puro

> Plan de implementacion para eliminar AWS SAM y CloudFormation del
> backend serverless del portfolio. devtools pasa a gestionar cada
> recurso AWS con AWS CLI imperativo, usando los YAML del repo como
> fuente de verdad y un archivo de estado local para decidir
> create / update / no-op.

## Estado

| Fase | Descripcion | Estado |
|------|-------------|--------|
| 0 | Spec (este documento) | HECHO |
| 1 | Capa base: `aws_cli.py` + `state.py` | Pendiente |
| 2 | `provisioner.py` + rename `lambda.yaml` -> `manifest.yaml` | Pendiente |
| 3 | `infra_provision.py` (resources/ -> llamadas AWS CLI) | Pendiente |
| 4 | `run-local` sin SAM (RIE / ejecucion directa) | Pendiente |
| 5 | Integracion CLI: `main.py` + `flags.py` + `help.py` | Pendiente |
| 6 | Eliminar SAM + CloudFormation del repo | Pendiente |
| 7 | Docs + rules + skill + CLAUDE.md | Pendiente |
| 8 | Refactor de tests + verificacion E2E iterativa | Pendiente |

Rama base sugerida: `feature/serverless-drop-sam` (parte de `dev`).

## Navegacion

| Documento | Cuando leer |
|-----------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Por que se elimina SAM, que se gana y que se pierde |
| [02-arquitectura-objetivo.md](02-arquitectura-objetivo.md) | Como queda el backend sin SAM: modulos, estado, flujo |
| [03-fase-1-capa-base.md](03-fase-1-capa-base.md) | `aws_cli.py` + `state.py` |
| [04-fase-2-provisioner-lambda.md](04-fase-2-provisioner-lambda.md) | `provisioner.py`: lambda.yaml -> AWS CLI |
| [05-fase-3-provisioner-infra.md](05-fase-3-provisioner-infra.md) | `infra_provision.py`: resources/ -> AWS CLI |
| [06-fase-4-run-local.md](06-fase-4-run-local.md) | `run-local` sin `sam local invoke` |
| [07-fase-5-integracion-cli.md](07-fase-5-integracion-cli.md) | Reconexion del CLI: comandos, flags, help |
| [08-fase-6-eliminar-sam.md](08-fase-6-eliminar-sam.md) | Borrar `sam_generate.py`, templates, Transform |
| [09-fase-7-docs.md](09-fase-7-docs.md) | rules, docs, skill, CLAUDE.md |
| [10-commits.md](10-commits.md) | Listado de commits incrementales |
| [11-paralelizacion-worktrees.md](11-paralelizacion-worktrees.md) | Desde que fase se puede usar worktrees |
| [12-fase-8-refactor-tests-y-verificacion.md](12-fase-8-refactor-tests-y-verificacion.md) | Refactor de TODOS los tests + ejecutar los comandos reales hasta que todo pase |

## Contexto breve

El backend ya esta a mitad de camino: la infra compartida se deploya con
`aws cloudformation deploy` directo (sin SAM), el build lo arma devtools
con `uv`, y `invoke-remote` usa `aws lambda invoke`. SAM solo aporta hoy
tres cosas: la macro `AWS::Serverless::Function`, `sam deploy` (subir el
zip + CloudFormation) y `sam local invoke`. El detalle completo de la
motivacion esta en [01-contexto-y-decision.md](01-contexto-y-decision.md).

## Decisiones tomadas (no reabrir)

- Se elimina **SAM y CloudFormation** por completo. devtools gestiona
  cada recurso con AWS CLI imperativo.
- devtools mantiene un **archivo de estado local** por
  `(scope, stage)` en `serverless/lambda/.state/` (gitignored).
- La migracion de la infra ya desplegada es **recrear desde cero**: se
  destruyen los stacks CloudFormation actuales (la data de DynamoDB es
  descartable) y se reaprovisiona con devtools.
- Cada necesidad de infra tiene su **archivo YAML propio** (esquema de
  devtools, sin `Transform` ni funciones intrinsecas de CloudFormation).
- `run-local` deja de usar `sam local invoke`: pasa a AWS Lambda RIE
  (Runtime Interface Emulator) via Docker, con fallback a ejecucion
  directa del handler en el `.venv`.

## Reglas criticas

- SIEMPRE verificar Python de devtools con `devtools/.venv/bin/python`
  (3.14), nunca `python3` del shell.
- NUNCA atribucion de IA en commits, PRs ni docstrings.
- Conventional Commits en espanol (subject + body).
- El `.state/` es efimero por entorno: gitignored, regenerable. NUNCA
  commitearlo.
- Cada llamada AWS pasa por `aws_cli.py` (perfil + region + manejo de
  error centralizados). NUNCA `subprocess.run(['aws', ...])` disperso.
- Antes de declarar una fase lista: tests verdes + Ruff + mypy sobre
  `devtools/serverless/` (ver [.claude/rules/verify-before-done.md](../../../.claude/rules/verify-before-done.md)).
- **Verificacion incremental OBLIGATORIA**: cada fase ejecuta, ademas
  de sus tests unitarios, los comandos reales de
  `python devtools/run.py serverless ...` que ya son posibles en ese
  punto. NO se acumula la verificacion para el final. Ninguna fase se
  declara lista mientras un comando que deberia funcionar en ese punto
  falle. Ver la matriz abajo.

## Verificacion incremental por fase

Cada fase trae una seccion "Verificacion incremental con comandos
devtools" que ejecuta lo que ya es posible. La matriz:

| Fase | Comandos `serverless` verificables al cerrarla |
|------|------------------------------------------------|
| 1 | `serverless help`, `tests --type=unit/coverage` (suite devtools) |
| 2 | + `tests --type=unit` (los 4 lambdas, tras el rename), `tests --shared` |
| 3 | + `provision-infra --dry-run`; con AWS: `provision-infra` real en dev |
| 4 | + `run --stage=local --runtime-mode=direct`; con Docker: `--runtime-mode=rie` |
| 5 | + `deploy --dry-run`, `status`; con AWS: `deploy`/`destroy`/`run --stage=dev` reales |
| 6 | + `init` (sin SAM); re-corre toda la bateria sin SAM instalado |
| 7 | (docs) — re-corre `tests` + `help` para confirmar que nada se rompio |
| 8 | bateria COMPLETA B.1 + B.2, iterando hasta que todo pase |

Regla: los comandos sin AWS (`--dry-run`, `help`, `tests`, `run-local
--runtime-mode=direct`) son OBLIGATORIOS en cada fase que los habilita.
Los que tocan AWS se ejecutan si hay acceso a la cuenta dev en el
momento; si no, se documentan como pendientes y se corren antes del
merge (Fase 8). La Fase 8 NO sustituye estas verificaciones: las
consolida y agrega la bateria E2E completa.

## Relacion con `serverless-restructure`

Esta spec asume el layout `serverless/lambda/{services,shared,resources}/`
que dejo el commit 1 de [serverless-restructure](../serverless-restructure/README.md).
Si `serverless-restructure` (commits 2-5) no esta mergeado aun, esta
migracion se puede hacer igual: solo se solapa en `flags.py` / `main.py` /
`help.py`. Recomendacion: cerrar `serverless-restructure` primero, o
asumir su diseno de CLI como contrato. Ver
[11-paralelizacion-worktrees.md](11-paralelizacion-worktrees.md).
