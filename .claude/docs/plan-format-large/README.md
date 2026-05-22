# Estandar de Plan de Implementacion (formato extendido)

> Documento maestro del formato de plan del portfolio. Detalla las tres
> secciones de ejecucion que TODO plan debe incluir — commits, paralelizacion
> con git worktrees y verificacion E2E iterativa — mas la descomposicion para
> paralelizacion. Referenciado desde `.claude/rules/plan-format.md`.

## Que define este documento

`.claude/rules/plan-format.md` define la estructura general y las secciones
1-7. Este documento define en detalle las secciones de **ejecucion**, que son
obligatorias en todo plan (Micro incluido, en forma minima):

| Seccion del plan | Que cubre | Detalle aqui |
|------------------|-----------|--------------|
| 8. Descomposicion para Paralelizacion | Tareas atomicas, checks de file-exclusivity | Capitulo 1 |
| 9. Commits | Listado de commits incrementales, cada uno verde | Capitulo 2 |
| 10. Paralelizacion con git worktrees | Base secuencial, que se paraleliza, como lanzar | Capitulo 3 |
| 11. Verificacion E2E iterativa (fase final) | Refactor de tests + bateria de comandos, bucle "no parar" | Capitulo 4 |

> Las secciones 9, 10 y 11 nacieron de fases que el plan `serverless-drop-sam`
> ejecuto "fuera de lo planificado" y resultaron criticas. Por eso ahora son
> parte obligatoria del formato: ningun plan se considera completo sin ellas.

## Regla maestra: todo plan vive en una carpeta

Todo plan se materializa como una **carpeta** `docs/specs/<nombre-kebab>/`,
no como un archivo suelto:

```text
docs/specs/<nombre-kebab>/
├── README.md                 # indice + estado + decisiones + matriz de verificacion
├── 01-contexto-y-decision.md # secciones 1-3 del plan (contexto, solucion, AC)
├── 02-<fase>.md              # una fase de implementacion por archivo
├── ...
├── NN-commits.md             # SECCION 9 (ver capitulo 2)
├── NN-paralelizacion-worktrees.md  # SECCION 10 (ver capitulo 3)
└── NN-verificacion-e2e.md    # SECCION 11 (ver capitulo 4)
```

Reglas de la carpeta:

- El `README.md` es el indice navegable: tabla "Cuando leer", tabla de estado
  por fase, decisiones tomadas (no reabrir), reglas criticas, matriz de
  verificacion incremental.
- Cada `.md` < 300 lineas (regla de `markdown-docs.md`). Si una fase es mas
  larga, se parte.
- Para planes **Micro** (1-2 archivos): la carpeta puede tener solo
  `README.md` con todo adentro — pero las secciones 9, 10 y 11 siguen
  presentes, en forma minima (1 commit, `worktrees: N/A`, verificacion corta).
- Para planes **Small/Medium/Large**: un `.md` por fase + los tres archivos
  de ejecucion (commits, worktrees, verificacion).

## Ciclo de vida de la carpeta: se elimina al mergear

La carpeta `docs/specs/<nombre-kebab>/` es un artefacto **efimero del plan**,
no documentacion permanente del producto. Una vez que el plan esta
implementado y su PR `feature/<nombre> -> dev` se mergea, la carpeta del plan
debe **eliminarse**:

- El ultimo commit del PR (el de la seccion 11) incluye el `git rm -r` de la
  carpeta `docs/specs/<nombre>/`, o se hace un commit de limpieza dedicado
  inmediatamente despues del merge.
- La fuente de verdad del cambio implementado pasa a ser el codigo, los
  tests, las rules y la documentacion de producto (`docs/cv/`, `docs/guide/`,
  etc.) — NO la spec. Si algo de la spec debe sobrevivir (una decision de
  arquitectura, una convencion), se promueve a una rule o a un doc de
  producto ANTES de borrar la carpeta.
- El plan en si queda en el historial de git: `git log` y el PR mergeado
  conservan la trazabilidad. No se necesita la carpeta viva.
- Las specs de planes **aun no implementados** (o en curso) SI permanecen en
  `docs/specs/`. La eliminacion aplica solo al mergear el plan completo.

Asi `docs/specs/` nunca acumula planes obsoletos: contiene unicamente lo que
esta pendiente o en ejecucion.

---

# Capitulo 1 — Seccion 8: Descomposicion para Paralelizacion

Obligatoria en Small/Medium/Large. En Micro: `N/A — cambio atomico`.

## Reglas de paralelizabilidad

Cada tarea debe pasar 3 checks antes de marcarse como paralelizable:

1. **File Exclusivity**: archivos de escritura no se solapan con tareas concurrentes
2. **Interface Stability**: no cambia firmas/contratos de API que afecten otras tareas
3. **Bounded Scope**: archivos y directorios claramente delimitados

## Estructura de cada tarea

Cada tarea incluye 6 campos obligatorios:

- **Archivos**: paths exactos donde se va a escribir
- **AC referenciados**: AC-X, AC-Y de la seccion 3 del plan
- **Depende de**: lista de tareas que deben completarse primero (o `ninguna`)
- **Paralelizable con**: lista de tareas concurrentes seguras (o `ninguna`)
- **Verify**: comando ejecutable de verificacion
- **Done**: criterio observable de completitud

## Plantilla de seccion 8

```markdown
## 8. Descomposicion para Paralelizacion

### Tareas (orden topologico)

#### T1: Crear modelo y schema
- **Archivos**: `src/content/config.ts`, `src/content/projects/*.md`
- **AC referenciados**: AC-1, AC-2
- **Depende de**: ninguna (raiz)
- **Paralelizable con**: T2 (no se solapan archivos)
- **Verify**: `pnpm run build` valida entries contra schema
- **Done**: schema creado, build exitoso, entry de ejemplo renderiza

#### T2: Crear utilities de formato
- **Archivos**: `src/lib/format-date.ts`, `tests/unit/lib/format-date.test.ts`
- **AC referenciados**: AC-3
- **Depende de**: ninguna (raiz)
- **Paralelizable con**: T1
- **Verify**: `pnpm exec vitest run tests/unit/lib/format-date.test.ts`
- **Done**: utility creada, tests verdes, coverage >= 80%

#### T3: Componente que consume schema + utilities
- **Archivos**: `src/components/ProjectCard.astro`
- **AC referenciados**: AC-1, AC-2, AC-3
- **Depende de**: T1, T2
- **Paralelizable con**: ninguna (depende de raices)
- **Verify**: `pnpm exec astro check` + `pnpm run build`
- **Done**: componente renderiza, typecheck limpio
```

## Reglas de granularidad y limites

- Granularidad por tamano de plan: Small=3-5 tareas, Medium=5-10, Large=10-20
- Si supera 20 tareas, descomponer en multiples planes (Huge)
- Limite practico de paralelizacion: **5-7 agentes concurrentes** (el overhead
  de review crece despues)
- Tareas raiz (sin dependencias) primero — habilitan paralelismo inmediato
- NUNCA mas de un agente escribiendo en el mismo archivo simultaneamente

## Anti-patrones de descomposicion

- Tareas con archivos solapados marcadas como "Paralelizable con" → race conditions
- Tareas que cambian interfaces publicas concurrentemente con consumidores → builds rotos
- "Paralelizable con: todas" sin verificacion real → falso positivo
- Tareas hoja (que dependen de muchas otras) marcadas como urgentes → bloquean el grafo

---

# Capitulo 2 — Seccion 9: Listado de Commits

Obligatoria en TODO plan. Archivo dedicado: `NN-commits.md` (o subseccion del
README en planes Micro).

## Que es

Una secuencia explicita de commits incrementales que implementan el plan. Cada
commit:

- Tiene su mensaje en Conventional Commits espanol (subject + body), ya
  redactado en el plan.
- Deja el repo en **estado verde** (lint + typecheck + tests del scope tocado).
- Es lo mas atomico y revisable posible (un commit = un cambio coherente).
- Indica que AC de la seccion 3 cubre.

## Regla por commit

Antes de cada commit se ejecuta, ademas de la suite del scope:

1. La verificacion del tipo de archivo (`.claude/rules/verify-before-done.md`).
2. La **verificacion incremental** de la fase correspondiente — los comandos
   reales que ya son posibles en ese punto del plan. NO se difiere la
   verificacion al final.

Ningun commit deja el repo roto. Si una migracion grande mantiene el sistema
viejo y el nuevo en paralelo, eso se declara explicitamente (ej.
`serverless-drop-sam`: hasta el commit 9, el CLI viejo seguia funcionando).

## Plantilla de seccion 9

```markdown
## 9. Commits

Rama base: `feature/<nombre>` desde `dev`.

### Commit 1 — `docs(specs): plan de <nombre>`
- Agrega `docs/specs/<nombre>/` (esta carpeta de plan).
- Sin cambios de codigo.

### Commit 2 — `feat(<scope>): <subject>`
- Crea `src/lib/<archivo>.ts` + su test mirror.
- Verde: AC-1, AC-2.
- Verificacion incremental: `pnpm exec vitest run tests/unit/lib/<archivo>.test.ts`

### Commit 3 — `feat(<scope>): <subject>`
- Modifica `src/components/<Componente>.astro`.
- Verde: AC-3.
- Verificacion incremental: `pnpm exec astro check` + `pnpm run build`

### Resumen de la secuencia

​```text
1  docs plan                 (sin codigo)
2  utility + test            cubre AC-1, AC-2
3  componente                cubre AC-3
4  refactor de tests + verificacion E2E   (seccion 11)
​```

## PR

Un solo PR `feature/<nombre> -> dev`. Body siguiendo
`.claude/rules/git-workflow.md` (Problema / Solucion / Como probar / TODO).
La seccion "Como probar" incluye la bateria de comandos de la seccion 11. El
PR NO se mergea hasta que esa bateria pasa completa.
```

## Reglas de la seccion 9

- El primer commit suele ser la propia carpeta del plan (`docs(specs): ...`).
- El ultimo commit es el de la seccion 11 (refactor de tests + verificacion);
  ese commit ademas elimina la carpeta `docs/specs/<nombre>/` con `git rm -r`
  (la spec es efimera — ver "Ciclo de vida de la carpeta" arriba). Si por
  flujo se prefiere un commit de limpieza separado, va inmediatamente despues
  del merge a `dev`.
- Los commits operativos que NO son de codigo (ej. "destruir y reaprovisionar
  infra") se listan igual, marcados como operativos.
- NUNCA atribucion de IA en los mensajes (politica de empresa).
- En Micro: la seccion puede ser un solo commit; igual se documenta. Ese
  commit unico tambien elimina la carpeta del plan al cerrarse.

---

# Capitulo 3 — Seccion 10: Paralelizacion con git worktrees

Obligatoria en TODO plan. Archivo dedicado: `NN-paralelizacion-worktrees.md`
(o subseccion del README en Micro, donde sera `N/A — cambio secuencial`).

## Que define

Desde que commit se puede empezar a paralelizar la implementacion con git
worktrees / subagentes concurrentes, y que fases son worktree-safe.

## Regla base: la base secuencial

Antes de lanzar cualquier worktree hay que identificar la **base secuencial**:
los commits que TODOS los worktrees necesitan o que tocan archivos
transversales. Tipicamente:

- El/los commit(s) que crean modulos compartidos de los que el resto importa.
- Cualquier commit con un diff **mecanico pero transversal** (ej. un rename
  que toca muchos archivos) — colisionaria con todo worktree, va secuencial.

```text
Commit 1 (plan) ............ sin codigo
Commit 2 (base compartida) ...... BASE — secuencial
Commit 3 (rename transversal) ... BASE — secuencial
   |
   +--- desde aqui se lanzan worktrees ---
```

## Que se puede paralelizar

Una fase es worktree-safe si toca archivos **disjuntos** de las demas fases
concurrentes. Se documenta en una tabla:

| Tarea | Archivos nuevos | Archivos modificados | Colision |
|-------|-----------------|----------------------|----------|
| Fase A (commit 4) | `a.ts`, tests | `shared.ts` | — |
| Fase B (commit 5) | `b.ts`, tests | `config.ts` | — |
| Fase C (commit 6) | `c.ts`, tests | — | — |

Si dos fases tocan el mismo archivo, NO se paralelizan: una espera a la otra.

## Que NO se paraleliza

- Las fases que tocan archivos transversales (grilla de comandos CLI, config
  central, barrel exports) — secuenciales por definicion.
- La seccion 11 (verificacion E2E) — depende de TODO integrado, va al final.
- Las fases de limpieza/borrado — solo tienen sentido con lo nuevo funcionando.

## Plantilla de seccion 10

```markdown
## 10. Paralelizacion con git worktrees

### Base secuencial (rama feature/<nombre>)
- commit 1  plan
- commit 2  base compartida          <- BASE
- commit 3  rename transversal       <- BASE

### Fase paralela (worktrees, lanzables tras commits 2 y 3)
- worktree A: Fase A  -> commit 4   (toca a.ts, shared.ts — disjunto)
- worktree B: Fase B  -> commit 5   (toca b.ts, config.ts — disjunto)
- worktree C: Fase C  -> commit 6   (toca c.ts — disjunto)

### Fase secuencial final
- merge de worktrees A, B, C en orden
- commit 7  reconexion (toca archivos transversales) <- requiere A+B+C
- commit 8  verificacion E2E (seccion 11)

Maximo paralelismo util: 3-4 worktrees.
```

## Como lanzar un worktree

```bash
# desde la raiz, con la base secuencial ya commiteada
git worktree add ../portfolio-wt-<fase> feature/<nombre>
cd ../portfolio-wt-<fase>
git checkout -b feature/<nombre>-<fase>
# ... implementar la fase ...
# al terminar: merge a feature/<nombre> como el commit que corresponda
```

O con un subagente: `Agent` con `isolation: "worktree"`, prompt = el contenido
del `.md` de la fase correspondiente.

## Reglas al integrar worktrees

- Integrar en el orden del listado de commits (seccion 9).
- Tras cada merge: correr la suite completa del scope — los modulos nuevos
  coexisten, no deben colisionar.
- Los toques minimos a archivos transversales (un import nuevo) se aplican
  AL INTEGRAR el worktree, no dentro de el, para no chocar con la fase de
  reconexion.

## Anti-patrones de worktrees

- Lanzar worktrees antes de que la base secuencial este commiteada → conflictos
- Dos worktrees tocando el mismo archivo → merge hell
- Worktree que toca la grilla de comandos / config central → debe ser secuencial
- Mas de 7 worktrees concurrentes → la coordinacion humana es el cuello de botella

---

# Capitulo 4 — Seccion 11: Verificacion E2E iterativa (fase final)

Obligatoria en TODO plan. Archivo dedicado: `NN-verificacion-e2e.md` (o
subseccion del README en Micro). Es SIEMPRE la ultima fase y el ultimo commit.

## Que es

La fase de cierre del plan. Dos partes obligatorias:

1. **Refactor de TODOS los tests** afectados: que ningun test viejo quede
   referenciando codigo eliminado, que los tests nuevos esten en la ruta y
   convencion correctas, que la suite completa siga verde tras integrar todo.
2. **Verificar que todo funciona** ejecutando los comandos / flujos reales —
   NO se detiene hasta que cada uno pasa (bucle "no parar hasta que funcione").

## Por que existe (no es redundante con la verificacion incremental)

Cada fase ya ejecuta su verificacion incremental (regla de la seccion 9). Pero
esa verificacion es **por fase y parcial**. Esta seccion NO la sustituye — la
**consolida** y cubre lo que ninguna fase individual puede:

- **Refactor global de tests**: solo posible con TODO el codigo integrado.
- **Bateria E2E en una sola corrida**: la secuencia completa de punta a punta
  con el codigo final, no porciones aisladas.
- **Regla de cierre del PR**: iterar corrigiendo hasta que toda la bateria
  pase. Es el gate que decide si el PR esta listo.

## Plantilla de seccion 11

```markdown
## 11. Verificacion E2E iterativa

### Parte A — refactor de tests

| Archivo | Accion |
|---------|--------|
| `tests/unit/<viejo>.test.ts` | ELIMINAR — el modulo bajo test ya no existe |
| `tests/unit/<modificado>.test.ts` | MODIFICAR — cubrir la nueva firma |
| `tests/unit/<nuevo>.test.ts` | CREAR — tests de la feature |

Barrido global (cero resultados esperados):

​```bash
rg -l "<simbolo-eliminado>" src/ tests/
​```

### Parte B — bateria de comandos reales

​```bash
# Verificacion del scope
pnpm exec biome check .
pnpm exec tsc --noEmit
pnpm exec astro check
pnpm exec vitest run --coverage      # >= 80% per-file
pnpm run build                       # build estatico exitoso

# E2E si el plan toca flujos de usuario
python devtools/run.py docker up --env=local
python devtools/run.py test_runner --module=feature --type=feature --env=local
​```

### Parte C — bucle de correccion ("no parar hasta que funcione")

​```text
ejecutar comando
   |
   v
{paso?}--si--> siguiente comando
   |
   no
   |
   v
diagnosticar (leer stderr, el output)
   |
   v
corregir codigo o test
   |
   v
re-ejecutar la suite + el comando que fallo
   |
   +-----------> volver a "ejecutar comando"
​```

### Regla de cierre

Esta fase NO se marca completa mientras quede un comando fallando, un test
rojo, o el coverage por debajo de 80%. Iterar — corregir, re-ejecutar,
repetir — hasta que toda la bateria pase. Solo entonces el PR esta listo.
```

## Reglas de la seccion 11

- Es SIEMPRE la ultima fase y el ultimo commit del listado de la seccion 9.
- La Parte B se divide en comandos que NO requieren recursos externos (corren
  siempre) y los que SI (AWS, Docker, deploy). Los primeros son obligatorios;
  los segundos se ejecutan si hay acceso, o se documentan como pendientes en
  el PR y se corren antes del merge.
- El "Como probar" del body del PR reutiliza la bateria de comandos de aqui.
- En Micro: la fase es minima — un barrido + la verificacion del scope + la
  regla de cierre. Sigue siendo obligatoria.

## Anti-patrones de la verificacion final

- Declarar el plan "listo" sin ejecutar la bateria completa
- Diferir TODA la verificacion al final (cada fase verifica lo suyo; esta solo
  consolida)
- Dejar tests referenciando codigo eliminado
- Mergear el PR con comandos de la bateria fallando
- Saltar el bucle de correccion ("se ve bien, lo dejo asi")

---

# Referencias

- `.claude/rules/plan-format.md` — regla principal (estructura, secciones 1-7)
- `.claude/rules/git-workflow.md` — Conventional Commits, flujo de PR
- `.claude/rules/verify-before-done.md` — verificacion por tipo de archivo
- `.claude/rules/harness-protocol.md` — subagentes con output en disco
- `.claude/rules/markdown-docs.md` — formato de la carpeta del plan
- Workflow Anthropic: Explore → Plan → Implement → Commit
