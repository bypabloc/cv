# 10 — Listado de commits

> [Anterior: 09](09-fase-7-docs.md) | [README](README.md) | [Siguiente: 11](11-paralelizacion-worktrees.md)

Commits incrementales para ejecutar la migracion. Cada commit deja el
repo en estado verde (tests + Ruff + mypy). Conventional Commits en
espanol. Rama base: `feature/serverless-drop-sam` desde `dev`.

## Regla por commit

Antes de cada commit, ademas de la suite unitaria
(`devtools/.venv/bin/python -m pytest devtools/tests/unit/src/serverless/`
verde + `python devtools/run.py docker lint --module=devtools` sin
errores), se ejecuta la **"Verificacion incremental con comandos
devtools"** de la fase correspondiente — los comandos reales de
`python devtools/run.py serverless ...` que ya son posibles en ese
punto (ver la matriz en el [README](README.md) y la seccion homonima de
cada fase). NO se acumula la verificacion para el final. Ningun commit
deja el CLI roto: hasta el commit 9, el CLI viejo (SAM) sigue
funcionando en paralelo al nuevo.

## Commits

### Commit 1 — `docs(specs): plan de migracion para eliminar SAM`

- Agrega `docs/specs/serverless-drop-sam/` (este conjunto de archivos).
- Sin cambios de codigo. Es el commit que ya contiene esta spec.

### Commit 2 — `feat(devtools): wrapper aws_cli + estado local serverless`

Fase 1. Toca solo archivos nuevos + un `.gitignore`.

- Crea `devtools/serverless/aws_cli.py`.
- Crea `devtools/serverless/state.py`.
- Crea `serverless/lambda/.state/.gitignore`.
- Crea `devtools/tests/unit/src/serverless/test_aws_cli.py` y `test_state.py`.
- Verde: AC-1.1..AC-1.11.

### Commit 3 — `refactor(serverless): renombra lambda.yaml a manifest.yaml`

Fase 2, sub-tarea del rename. Commit aislado (diff mecanico, facil de
revisar) ANTES del provisioner.

- `git mv` de los 4 `serverless/lambda/services/*/lambda.yaml` ->
  `manifest.yaml`.
- `git mv` de `.claude/templates/lambda-controller/lambda.yaml` ->
  `manifest.yaml`.
- Define `MANIFEST_FILENAME = 'manifest.yaml'` en
  `devtools/serverless/resolve.py`.
- Actualiza los 6 modulos de devtools que buscaban `'lambda.yaml'`
  (`shared_resolver.py`, `vendoring.py`, `lifecycle.py`,
  `lambda_controller.py`, `packaging.py`, `flags.py`) para importar la
  constante. `sam_generate.py` NO se toca (se elimina en el commit 9).
- Verde: AC-2.11, AC-2.12 + `serverless tests --type=unit` sigue verde.

### Commit 4 — `feat(devtools): provisioner de Lambdas con AWS CLI`

Fase 2. Reemplaza la traduccion a SAM por llamadas AWS CLI directas.

- Crea `devtools/serverless/provisioner.py`.
- Modifica `devtools/serverless/packaging.py` (agrega `zip_build_dir`,
  `build.zip`).
- Crea `devtools/tests/unit/src/serverless/test_provisioner_render.py` y
  `test_provisioner_provision.py`.
- `sam_generate.py` sigue existiendo: el CLI viejo no se rompe todavia.
- Verde: AC-2.1..AC-2.10.

### Commit 5 — `feat(devtools): provisioner de infra compartida con AWS CLI`

Fase 3. Reemplaza el deploy CloudFormation de la infra.

- Crea `devtools/serverless/infra_provision.py`.
- Reescribe los 7 fragmentos de `serverless/lambda/resources/` al esquema
  devtools; elimina `_header.yaml`.
- Elimina `devtools/serverless/infra_deploy.py`.
- Crea `devtools/tests/unit/src/serverless/test_infra_render.py` y
  `test_infra_provision.py`.
- **Punto de atencion**: `main.py` importa `infra_deploy`. Para no
  romper el CLI en este commit, `main.py` se actualiza aqui mismo
  (import a `infra_provision`, comando `deploy-infra` apunta a
  `cmd_provision_infra`). Es un toque minimo de `main.py`; el resto de la
  reconexion del CLI es el commit 8.
- Verde: AC-3.1..AC-3.7.

### Commit 6 — `feat(devtools): run-local sin SAM (RIE + modo directo)`

Fase 4. Reemplaza `sam local invoke`.

- Crea `devtools/serverless/local_runtime.py`.
- Crea `devtools/tests/unit/src/serverless/test_local_runtime.py`.
- NO toca `lambda_controller.py` todavia (eso es el commit 8).
- Verde: AC-4.1..AC-4.5.

### Commit 7 — `test(devtools): cobertura de integracion provisioner+state`

Opcional pero recomendado. Tests que cruzan `provisioner` + `state` +
`packaging` end-to-end con AWS CLI mockeado, antes de reconectar el CLU.

- Amplia `devtools/tests/unit/src/serverless/` con tests de flujo completo del
  diff `CREATE`/`UPDATE_*`/`NOOP`.

### Commit 8 — `refactor(devtools): CLI serverless usa provisioner, elimina SAM`

Fase 5. El commit que conecta todo. Toca la grilla de comandos.

- Modifica `devtools/serverless/lambda_controller.py`: `deploy` y `run`
  usan `provisioner` / `local_runtime` / `state`; elimina
  `cmd_sam_generate` y los `_ensure_tool('sam', ...)`; agrega
  `cmd_destroy` y `cmd_status`.
- Modifica `devtools/serverless/main.py`: `COMMAND_REGISTRY` —
  `provision-infra`, `destroy`, `status`; quita `sam-generate`.
- Modifica `devtools/serverless/flags.py`: quita `guided`/`debug`,
  agrega `runtime-mode`/`yes`, registra los comandos nuevos.
- Modifica `devtools/serverless/help.py`: textos sin SAM.
- Amplia `devtools/tests/unit/src/serverless/test_flags.py` y crea/amplia
  `test_lambda_controller.py`.
- A partir de aqui el CLI nuevo es el unico. `sam_generate.py` queda
  huerfano (se borra en el commit 9).
- Verde: AC-5.1..AC-5.7.

### Commit 9 — `chore(serverless): elimina SAM y CloudFormation del repo`

Fase 6. Limpieza.

- Elimina `devtools/serverless/sam_generate.py`.
- Borra cualquier `template.yaml` / `.aws-sam/` efimero residual del
  working tree (ninguno esta versionado — ver Fase 6).
- Limpia los `.gitignore` de los 4 services y `serverless/.gitignore`
  (`.aws-sam/`, `samconfig.toml`, `template.yaml`).
- Modifica `lifecycle.py`: `cmd_init` deja de verificar `sam`.
- Actualiza el comentario de cabecera de los `manifest.yaml` (ya
  renombrados desde `lambda.yaml` en el commit 3).
- Verde: AC-6.1..AC-6.3, AC-6.5, AC-6.6 (AC-6.4 es E2E manual).

### Commit 10 — `docs(serverless): documenta el backend sin SAM`

Fase 7. Toca solo `.claude/` y `CLAUDE.md` — disjunto del codigo.

- Actualiza `.claude/rules/lambda-controller.md`,
  `neon-management.md`, `serverless-secrets.md`.
- Actualiza `.claude/docs/lambda-controller/`,
  `.claude/docs/serverless-backend/`.
- Actualiza `.claude/skills/lambda-controller/SKILL.md`.
- Actualiza `.claude/templates/lambda-controller/`.
- Actualiza `CLAUDE.md`.
- Crea `.claude/docs/serverless-backend/05-estado-local.md`.
- Validacion `claude -p` (5 prompts, ver Fase 7).
- Verde: AC-7.1..AC-7.5.

### Commit 11 — `test(serverless): refactoriza tests del backend sin SAM`

Fase 8, Parte A. Refactor de TODOS los tests para reflejar el modelo sin
SAM.

- Elimina `devtools/tests/unit/src/serverless/sam_generate.py` (test del
  modulo borrado).
- Reconcilia los nombres de los archivos de test nuevos a la convencion
  de devtools (`aws_cli.py`, `state.py`, `provisioner.py`,
  `infra_provision.py`, `local_runtime.py`, `lambda_controller.py` —
  sin prefijo `test_`).
- Modifica `devtools/tests/unit/src/serverless/flags.py` y `packaging.py`.
- Revisa los `conftest.py` / `_helpers.py` / `_fixtures/` de los 4
  Lambdas y de `shared/`; refactoriza cualquiera que referencie SAM.
- Barrido global: cero referencias a `sam`/`template.yaml` en tests.
- Verde: AC-8.1..AC-8.5.

### Commit 12 — `chore(serverless): destruye stacks CFN y reaprovisiona`

Fase 8, Parte B (la parte que toca AWS) + Fase 6 operativa. No es un
commit de codigo: ejecuta la bateria de comandos reales del CLI contra
AWS dev, destruye los stacks CloudFormation y reaprovisiona con el CLI
nuevo. NO se detiene hasta que todos los comandos pasan (regla de cierre
de la Fase 8). Su resultado se documenta en el body del PR.

## Resumen de la secuencia

```text
1  docs spec                          (sin codigo)
2  aws_cli + state                    Fase 1
3  rename lambda.yaml -> manifest.yaml Fase 2 (sub-tarea)
4  provisioner lambda                 Fase 2
5  infra_provision + resources/       Fase 3   (toca main.py minimo)
6  local_runtime                      Fase 4
7  tests de integracion               (opcional)
8  reconexion CLI + elimina cmd SAM   Fase 5   (toca flags/main/help)
9  elimina sam_generate               Fase 6
10 docs / rules / skill / CLAUDE.md   Fase 7
11 refactor de TODOS los tests        Fase 8 Parte A
12 verificar comandos + reaprovisionar  Fase 8 Parte B + Fase 6 operativo
```

## PR

Un solo PR `feature/serverless-drop-sam -> dev` con los commits 1-11
(el 12 es operativo). Body del PR siguiendo
[.claude/rules/git-workflow.md](../../../.claude/rules/git-workflow.md):
Problema / Solucion / Como probar / TODO. La seccion "Como probar"
incluye la bateria de comandos B.1/B.2 de la
[Fase 8](12-fase-8-refactor-tests-y-verificacion.md). El PR NO se mergea
hasta que toda la bateria B.1 pasa y la B.2 esta verificada o
documentada como pendiente.

---

[Anterior: 09](09-fase-7-docs.md) | [README](README.md) | [Siguiente: 11](11-paralelizacion-worktrees.md)
