# Paralelizacion con git worktrees

> [Anterior: 04](04-commit-5-docs.md) | [README](README.md)

## Regla base

El commit 1 (estructura + paths) YA esta hecho y commiteado en
`feature/serverless-restructure` (`5b510f5`). Es la **base obligatoria**:
mueve carpetas que todos los demas commits tocan. Nada se podia
paralelizar sobre el — por eso se hizo secuencial y primero.

**A partir del commit 1 ya commiteado, se puede paralelizar.** Cada
worktree parte de `feature/serverless-restructure` (que ya tiene el
commit 1).

## Que se puede hacer en paralelo y que no

```
commit 1 (HECHO, base)
   |
   +-- commit 2  (CLI tests/run) ......... toca flags.py, main.py,
   |                                        help.py, lambda_controller.py
   |
   +-- commit 4  (drop db-*) ............. toca flags.py, main.py,
   |                                        help.py, database.py
   |
   +-- commit 3  (resources) ............. toca flags.py, main.py,
   |                                        help.py, infra_deploy.py,
   |                                        sam_generate.py, resolve.py,
   |                                        + los Lambdas
   |
   +-- commit 5  (docs) ................. toca .claude/, CLAUDE.md, docs/
```

### Conflicto: commits 2, 3 y 4 colisionan

Los commits **2, 3 y 4 los tres modifican `flags.py`, `main.py` y
`help.py`** (la grilla de comandos del CLI). Si se hacen en worktrees
paralelos, el merge sera conflictivo en esos 3 archivos.

Conclusion: **2, 3 y 4 NO se deben paralelizar entre si.** Van
secuenciales en la misma rama, en este orden recomendado:

1. Commit 2 (CLI tests/run) — establece la grilla nueva.
2. Commit 4 (drop db-*) — quita comandos de la grilla ya nueva.
3. Commit 3 (resources) — agrega `deploy-resource` a la grilla.

(2 antes que 4 porque 4 asume `run` ya existe. 3 al final porque es el
mas grande y arriesgado, y porque conviene tener el CLI estable antes.)

### Lo que SI se puede paralelizar

| Tarea | Worktree | Depende de | Toca |
|-------|----------|------------|------|
| Commit 5 (docs/rules/skill) | si | nada (solo de commit 1) | `.claude/`, `docs/`, `CLAUDE.md` |
| Commit 4 sub-tarea: extender Lambda `db` (controllers `seed`/`tables` + tests) | si | nada (solo de commit 1) | `serverless/lambda/services/db/` |
| Commit 3 sub-tarea: reescribir los 8 fragmentos YAML a stacks autonomos | si | nada (solo de commit 1) | `serverless/lambda/resources/` |

Esas 3 tareas tocan archivos **disjuntos** entre si y del CLI. Se pueden
lanzar en worktrees concurrentes apenas el commit 1 esta (ya lo esta).

### Restriccion del commit 5

El commit 5 (docs) describe el resultado final de 2/3/4. Si se hace en
paralelo ANTES de que 2/3/4 esten definidos, puede documentar algo que
luego cambie. Opciones:

- **Opcion A (recomendada)**: commit 5 al final, secuencial, cuando
  2/3/4 ya estan. Cero retrabajo.
- **Opcion B**: commit 5 en worktree paralelo, asumiendo el diseno de
  los docs 01-04 de esta carpeta como contrato. Riesgo: si la
  implementacion de 2/3/4 se desvia del plan, hay que reajustar los
  docs.

## Plan de ejecucion recomendado

```
Fase A — secuencial (rama feature/serverless-restructure):
  [HECHO] commit 1
  commit 2  (CLI tests/run)
  commit 4  (drop db-* en el CLI — la parte de devtools)
  commit 3  (resources — devtools + Lambdas)

Fase B — worktrees, lanzables apenas termina commit 1 (= ahora):
  worktree-1: extender Lambda db (seed/tables) -> se integra en commit 4
  worktree-2: reescribir fragmentos resources/ -> se integra en commit 3
  worktree-3: commit 5 docs (Opcion B) o dejar para Fase A final

Fase C — secuencial:
  merge de los worktrees a feature/serverless-restructure en el commit
  que corresponde (4 para worktree-1, 3 para worktree-2)
  commit 5 si se eligio Opcion A
  verificacion final + PR
```

Maximo paralelismo util: 3 worktrees (worktree-1, worktree-2,
worktree-3). Mas no aporta — el resto es secuencial por el conflicto en
`flags.py`/`main.py`/`help.py`.

## Como lanzar un worktree

```bash
# desde la raiz del repo, con commit 1 ya en feature/serverless-restructure
git worktree add ../portfolio-wt-db feature/serverless-restructure
# trabajar en ../portfolio-wt-db, branch propia:
cd ../portfolio-wt-db && git checkout -b feature/serverless-db-seed-tables
# al terminar: merge a feature/serverless-restructure en el commit 4
```

O con un agente: `Agent` con `isolation: "worktree"`, prompt = el
contenido del doc del commit correspondiente.

## Resumen para el usuario

- **Desde el commit 1 (ya hecho) se puede iniciar worktrees.**
- 3 tareas son worktree-safe: extender Lambda `db`, reescribir
  fragmentos `resources/`, y docs (con la salvedad de la Opcion A/B).
- Los commits 2, 3 y 4 **no** se paralelizan entre si: colisionan en
  `flags.py`/`main.py`/`help.py`. Van secuenciales: 2 -> 4 -> 3.

---

[Anterior: 04](04-commit-5-docs.md) | [README](README.md)
