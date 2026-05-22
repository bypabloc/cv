# 11 — Paralelizacion con git worktrees

> [Anterior: 10](10-commits.md) | [README](README.md) | [Siguiente: 12](12-fase-8-refactor-tests-y-verificacion.md)

A partir de que paso se puede paralelizar la implementacion con git
worktrees, y que tareas son worktree-safe.

## Regla base

La base obligatoria son DOS commits secuenciales:

- **Commit 2 — Fase 1** (`aws_cli.py` + `state.py`): las Fases 2, 3 y 4
  importan de ella.
- **Commit 3 — rename `lambda.yaml` -> `manifest.yaml`** (sub-tarea de
  la Fase 2): toca 6 modulos del CLI (`flags.py`, `lambda_controller.py`,
  `packaging.py`, `resolve.py`, `shared_resolver.py`, `vendoring.py`,
  `lifecycle.py`). Es un diff mecanico pero transversal — si se hiciera
  en un worktree, colisionaria con casi todos los demas. Va secuencial,
  justo despues del commit 2, en la rama base.

**No se puede paralelizar nada antes de que los commits 2 y 3 esten en
la rama.** El commit 3 deja los modulos del CLI ya apuntando a
`manifest.yaml`, asi los worktrees parten de un estado coherente.

```text
Commit 1 (spec) ............ sin codigo
Commit 2 (Fase 1: aws_cli + state) ...... BASE — secuencial
Commit 3 (rename lambda.yaml -> manifest.yaml) .. BASE — secuencial
   |
   +--- desde aqui se puede lanzar worktrees ---
```

## Que se puede paralelizar y que no

```text
Commits 2 + 3 (base secuencial)
   |
   +-- Fase 2 provisioner          worktree A  -> commit 4
   |     toca: provisioner.py (nuevo), packaging.py, tests nuevos
   |
   +-- Fase 3 (infra_provision)    worktree B  -> commit 5
   |     toca: infra_provision.py (nuevo), resources/*.yaml,
   |           infra_deploy.py (eliminar), tests nuevos
   |
   +-- Fase 4 (local_runtime)      worktree C  -> commit 6
   |     toca: local_runtime.py (nuevo), tests nuevos
   |
   +-- Fase 7 (docs)               worktree D  -> commit 10
         toca: .claude/, CLAUDE.md   (ver salvedad abajo)
```

### El provisioner, la Fase 3 y la Fase 4 SÍ se paralelizan entre si

Tocan archivos **disjuntos**:

| Tarea | Archivos nuevos | Archivos modificados | Colision |
|-------|-----------------|----------------------|----------|
| provisioner (commit 4) | `provisioner.py`, 2 tests | `packaging.py` | — |
| infra (commit 5) | `infra_provision.py`, 2 tests | `resources/*.yaml`, borra `infra_deploy.py` | — |
| run-local (commit 6) | `local_runtime.py`, 1 test | — | — |

Ninguna toca `flags.py` / `main.py` / `help.py` (salvo el toque MÍNIMO
de `main.py` en la Fase 3 para el import de `infra_provision` — ese toque
se hace al integrar el worktree B, no en paralelo). El rename del CLI ya
quedo resuelto en el commit 3 de la rama base, asi que ningun worktree
vuelve a tocar esos modulos por el rename. Se pueden lanzar 3 worktrees
concurrentes apenas los commits 2 y 3 estan.

### Lo que NO se paraleliza: la Fase 5

La **Fase 5** (commit 8) toca `flags.py`, `main.py`, `help.py` y
`lambda_controller.py` — la grilla de comandos. Es secuencial por
definicion: necesita que las Fases 2, 3 y 4 ya esten mergeadas (importa
de los tres modulos). Va sola, despues de integrar los worktrees.

### La Fase 6 (commit 9) tambien es secuencial

Borra `sam_generate.py` y limpia los `.gitignore`. Solo tiene sentido
cuando la Fase 5 ya dejo el CLI nuevo funcionando. No se paraleliza.

## La Fase 7 (docs) — salvedad

La Fase 7 describe el resultado final de las Fases 2-6. Dos opciones:

- **Opcion A (recomendada)**: Fase 7 al final, secuencial, cuando 2-6 ya
  estan. Cero retrabajo.
- **Opcion B**: Fase 7 en worktree D paralelo, asumiendo el diseno de los
  docs 02-08 de esta carpeta como contrato. Riesgo: si la implementacion
  se desvia del plan, hay que reajustar los docs y revalidar con
  `claude -p`.

Si se elige B, el worktree D se puede lanzar junto con A/B/C (toca solo
`.claude/` y `CLAUDE.md`, disjunto del codigo).

## Plan de ejecucion recomendado

```text
Fase secuencial inicial (rama feature/serverless-drop-sam):
  commit 1  spec
  commit 2  Fase 1 (aws_cli + state)                <- BASE
  commit 3  rename lambda.yaml -> manifest.yaml      <- BASE

Fase paralela (worktrees, lanzables tras los commits 2 y 3):
  worktree A: Fase 2 provisioner         -> integra como commit 4
  worktree B: Fase 3 (infra_provision)   -> integra como commit 5
  worktree C: Fase 4 (local_runtime)     -> integra como commit 6
  worktree D: Fase 7 (docs, Opcion B)    -> integra como commit 10
              (o dejar para el final, Opcion A)

Fase secuencial final (rama feature/serverless-drop-sam):
  merge de worktrees A, B, C en orden (commits 4, 5, 6)
  commit 7  tests de integracion (opcional)
  commit 8  Fase 5 (reconexion CLI)             <- requiere A+B+C
  commit 9  Fase 6 (eliminar SAM)
  commit 10 Fase 7 (docs, si se eligio Opcion A)
  commit 11 Fase 8 Parte A (refactor de TODOS los tests)
  commit 12 Fase 8 Parte B (verificar comandos) + destruir CFN +
            reaprovisionar (operativo)
  verificacion E2E final + PR
```

> La **Fase 8 NO se paraleliza**. La Parte A (refactor de tests) toca
> tests de todos los modulos y de los 4 Lambdas — depende de que las
> Fases 1-7 esten cerradas. La Parte B ejecuta los comandos reales del
> CLI y solo tiene sentido con todo integrado. Va secuencial al final,
> y su regla de cierre (iterar hasta que toda la bateria pase) gobierna
> cuando el PR esta listo.

Maximo paralelismo util: **3-4 worktrees** (A, B, C, y opcionalmente D).
Mas no aporta — el resto es secuencial por la dependencia de la Fase 5
sobre las tres y por la colision en la grilla de comandos.

## Respuesta directa: ¿desde que paso se puede usar worktree?

**Desde los commits 2 y 3 ya commiteados.** El commit 2 (Fase 1) y el
commit 3 (rename `lambda.yaml` -> `manifest.yaml`) son la base
obligatoria secuencial: el primero porque todos importan de el, el
segundo porque toca transversalmente 6 modulos del CLI y colisionaria
con cualquier worktree. Con ambos en la rama, se lanzan hasta 4
worktrees en paralelo (Fase 2 provisioner, Fase 3, Fase 4 y
opcionalmente Fase 7 docs). Las Fases 5 y 6 vuelven a ser secuenciales.

## Como lanzar un worktree

```bash
# desde la raiz del repo, con los commits 2 y 3 ya en
# feature/serverless-drop-sam
git worktree add ../portfolio-wt-provisioner feature/serverless-drop-sam
cd ../portfolio-wt-provisioner
git checkout -b feature/serverless-drop-sam-provisioner
# ... implementar la Fase 2 (provisioner) ...
# al terminar: merge a feature/serverless-drop-sam como commit 4
```

O con un agente: `Agent` con `isolation: "worktree"`, prompt = el
contenido del documento de la fase correspondiente
([04](04-fase-2-provisioner-lambda.md), [05](05-fase-3-provisioner-infra.md),
[06](06-fase-4-run-local.md)).

## Reglas al integrar los worktrees

- Integrar en orden 4 -> 5 -> 6 (no importa funcionalmente, pero
  mantiene el listado de commits coherente).
- Tras cada merge: correr la suite completa `devtools/tests/unit/src/serverless/`
  — los modulos nuevos coexisten, no deben colisionar.
- El toque minimo de `main.py` (import de `infra_provision`) se aplica
  al integrar el worktree B, no dentro del worktree, para evitar que B
  toque `main.py` y choque con la Fase 5.

---

[Anterior: 10](10-commits.md) | [README](README.md) | [Siguiente: 12](12-fase-8-refactor-tests-y-verificacion.md)
