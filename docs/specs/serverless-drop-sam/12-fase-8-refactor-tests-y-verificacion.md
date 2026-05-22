# 12 — Fase 8: refactor de tests + verificacion E2E iterativa

> [Anterior: 11](11-paralelizacion-worktrees.md) | [README](README.md)

Fase final y de cierre. Dos partes obligatorias:

1. **Refactorizar TODOS los tests** del backend serverless para que
   reflejen el modelo sin SAM (eliminar tests de `sam_generate`, alinear
   los de `provisioner`/`infra_provision`/`state`, revisar los de los
   Lambdas y de `shared/`).
2. **Verificar que todo funciona** ejecutando los comandos reales de
   `devtools/run.py serverless` — NO se detiene hasta que cada comando
   pasa.

Depende de las Fases 1-7 (todo el codigo y los docs ya estan).

## Por que esta fase existe (decision)

Cada fase (1-7) ya ejecuta su propia "Verificacion incremental con
comandos devtools": no se difiere la verificacion al final. Pero esa
verificacion incremental es por fase y parcial. Esta fase NO la
sustituye — la **consolida** y cubre lo que ninguna fase individual
puede:

- **Refactor global de tests**: que no quede ningun test viejo
  referenciando `sam_generate` o `template.yaml`, que los tests de los 4
  Lambdas + `shared/` sigan verdes tras `build/` -> `build.zip`, y que
  los archivos de test nuevos esten en la ruta y convencion correctas.
  Esto solo se puede hacer con TODO el codigo ya integrado.
- **Bateria E2E completa en una sola corrida**: cada fase verifico SU
  porcion del flujo; aqui se corre la secuencia entera
  (`provision-infra` -> `deploy` x4 -> `run` -> `status` -> `destroy` ->
  reaprovisionar) de punta a punta, con el codigo final.
- **Regla de cierre del PR**: iterar corrigiendo hasta que toda la
  bateria pase. Es el gate que decide si el PR esta listo.

La regla del usuario es explicita: **cada fase verifica con comandos
reales a medida que avanza** (eso lo cubren las secciones "Verificacion
incremental" de las Fases 1-7) **y al final se refactorizan todos los
tests y se re-ejecuta la bateria completa sin parar hasta que todo
funcione** (esta fase).

## Ubicacion real de los tests (corregido)

| Conjunto | Ruta | Que cubre |
|----------|------|-----------|
| Tests del CLI devtools | `devtools/tests/unit/src/serverless/` | `flags.py`, `packaging.py`, `resolve.py`, `sam_generate.py`, `shared_resolver.py`, `vendoring.py` |
| Tests de cada Lambda | `serverless/lambda/services/<lambda>/tests/{unit,integration}/` | controllers, services, models, handler |
| Tests de `shared/` | `serverless/lambda/shared/tests/unit/shared/` | cache, db, dynamodb, rate_limit, cors, etc. |

> NOTA sobre la convencion de nombres de archivo: los tests del CLI de
> devtools NO usan el prefijo `test_` ni el patron 1-archivo-por-escenario
> del estandar lambda-controller. Espejan el modulo bajo test:
> `devtools/serverless/<modulo>.py` -> `devtools/tests/unit/src/serverless/<modulo>.py`,
> con varias funciones `test_*` dentro. Por eso los archivos de test
> nuevos de esta migracion son `aws_cli.py`, `state.py`, `provisioner.py`,
> `infra_provision.py`, `local_runtime.py`, `lambda_controller.py` (sin
> prefijo `test_`), todos bajo `devtools/tests/unit/src/serverless/`.
> Las Fases 3-7 los nombran con prefijo `test_` por costumbre; esta fase
> reconcilia el nombre real al de la convencion de devtools.

## Parte A — refactor de tests

### A.1 — Tests del CLI devtools (`devtools/tests/unit/src/serverless/`)

| Archivo | Accion |
|---------|--------|
| `sam_generate.py` | **ELIMINAR** — el modulo ya no existe |
| `packaging.py` | **MODIFICAR** — cubrir `zip_build_dir`, ajustar a `build.zip` |
| `flags.py` | **MODIFICAR** — quitar tests de `sam-generate`/`guided`/`debug`, agregar `provision-infra`/`destroy`/`status`/`runtime-mode`/`yes` |
| `resolve.py` | **REVISAR** — probablemente sin cambios |
| `shared_resolver.py` | **REVISAR** — sin cambios |
| `vendoring.py` | **REVISAR** — sin cambios |
| `aws_cli.py` | **CREAR** — tests de Fase 1 |
| `state.py` | **CREAR** — tests de Fase 1 |
| `provisioner.py` | **CREAR** — tests de Fase 2 (render + provision) |
| `infra_provision.py` | **CREAR** — tests de Fase 3 (render + provision) |
| `local_runtime.py` | **CREAR** — tests de Fase 4 |
| `lambda_controller.py` | **CREAR/AMPLIAR** — tests de Fase 5 (`cmd_deploy`, `cmd_destroy`, `cmd_status`) |

Convencion del proyecto: un archivo de test por modulo (espeja
`devtools/serverless/<modulo>.py` -> `devtools/tests/unit/src/serverless/<modulo>.py`).
Si un modulo necesita varios escenarios, van como funciones `test_*`
dentro del mismo archivo (es la convencion de devtools, distinta del
estandar lambda-controller de 1 archivo por escenario).

### A.2 — Tests de los 4 Lambdas

Los tests de `core/` (controllers, services, models, handler) NO cambian
de logica — la migracion no toca el runtime de los Lambdas. Pero hay que
verificar que:

- Ningun `conftest.py` ni `_helpers.py` referencia `template.yaml`,
  `.aws-sam/` o `sam`.
- Los tests siguen verdes tras el cambio `build/` -> `build.zip` en
  `packaging.py` (los tests de Lambda no deberian depender de eso, pero
  se confirma).
- `tests/integration/` de cada Lambda: si algun fixture asumia un
  recurso creado por CloudFormation, se reapunta al recurso aprovisionado
  por devtools.

Lambdas: `contact_form`, `tracking_pixel`, `stream_processor`, `db`.

### A.3 — Tests de `shared/`

`serverless/lambda/shared/tests/unit/shared/` — revisar que ningun test
asuma SAM. Es improbable (la libreria comun no conoce el deploy), pero
se confirma con un grep.

### A.4 — Barrido global

```bash
rg -l "sam_generate|template\.yaml|aws-sam|sam local|sam deploy|Transform: AWS::Serverless" \
   devtools/tests/ serverless/lambda/*/tests/ serverless/lambda/shared/tests/
# Resultado esperado: 0 archivos
```

Cualquier archivo que aparezca se refactoriza o se elimina.

## Parte B — verificacion ejecutando comandos reales

Tras el refactor de tests, ejecutar la bateria completa de comandos
`serverless` de devtools. **No se detiene hasta que todos pasan.** Si uno
falla, se corrige el codigo o el test, se vuelve a ejecutar la suite, y
se repite.

### B.1 — Comandos que NO tocan AWS (corren siempre)

```bash
# Suite de tests completa
devtools/.venv/bin/python -m pytest devtools/tests/ -v
python devtools/run.py serverless tests --type=unit
python devtools/run.py serverless tests --type=coverage
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=unit --lambda=contact-form
python devtools/run.py serverless tests --type=unit --lambda=tracking-pixel
python devtools/run.py serverless tests --type=unit --lambda=stream-processor
python devtools/run.py serverless tests --type=unit --lambda=db

# Quality
python devtools/run.py serverless lint
python devtools/run.py serverless typecheck
python devtools/run.py docker lint --module=devtools

# CLI sin red
python devtools/run.py serverless help
python devtools/run.py serverless init
python devtools/run.py serverless deploy --lambda=contact-form --stage=dev --dry-run
python devtools/run.py serverless provision-infra --stage=dev --dry-run

# run-local (modo directo, sin Docker ni AWS)
python devtools/run.py serverless run --lambda=contact-form --stage=local \
  --event=events/create.json --runtime-mode=direct
```

### B.2 — Comandos que tocan AWS (contra dev, perfil `tfs-dev`)

Requieren la cuenta dev. Se ejecutan tras destruir los stacks
CloudFormation viejos (Fase 6 / commit 10).

```bash
export AWS_PROFILE=tfs-dev

# 1. Aprovisionar infra
python devtools/run.py serverless provision-infra --stage=dev --aws-profile=tfs-dev

# 2. Deployar los 4 lambdas (CREATE)
for L in contact-form tracking-pixel stream-processor db; do
  python devtools/run.py serverless deploy --lambda=$L --stage=dev --aws-profile=tfs-dev
done

# 3. Idempotencia: re-deploy sin cambios -> debe reportar NOOP
python devtools/run.py serverless deploy --lambda=contact-form --stage=dev --aws-profile=tfs-dev

# 4. run-local modo RIE (Docker)
python devtools/run.py serverless run --lambda=contact-form --stage=local \
  --event=events/create.json --runtime-mode=rie

# 5. Invocar cada lambda deployado
for L in contact-form tracking-pixel stream-processor db; do
  python devtools/run.py serverless run --lambda=$L --stage=dev \
    --event=events/<evento>.json --aws-profile=tfs-dev
done

# 6. status: estado local vs AWS
python devtools/run.py serverless status --stage=dev --aws-profile=tfs-dev

# 7. destroy + reaprovisionar (verifica el ciclo completo)
python devtools/run.py serverless destroy --stage=dev --yes --aws-profile=tfs-dev
python devtools/run.py serverless provision-infra --stage=dev --aws-profile=tfs-dev
```

### B.3 — Bucle de correccion (regla "no parar hasta que funcione")

```text
ejecutar comando
   |
   v
{paso?}--si--> siguiente comando
   |
   no
   |
   v
diagnosticar (leer stderr, el .state/, el output AWS)
   |
   v
corregir codigo o test
   |
   v
re-ejecutar la suite de tests + el comando que fallo
   |
   +-----------> volver a "ejecutar comando"
```

NO se declara la fase lista mientras un comando de B.1 o B.2 falle. Los
de B.1 son obligatorios siempre; los de B.2 requieren acceso AWS — si no
hay acceso en el momento, se documenta el resultado pendiente en el body
del PR y se ejecutan antes de mergear a `dev`.

## Archivos afectados

### Crear

- (los tests nuevos de Fases 1-5 se consolidan aqui en
  `devtools/tests/unit/src/serverless/`: `aws_cli.py`, `state.py`,
  `provisioner.py`, `infra_provision.py`, `local_runtime.py`,
  `lambda_controller.py`)

### Eliminar

- `devtools/tests/unit/src/serverless/sam_generate.py` — el modulo bajo
  test ya no existe.

### Modificar

- `devtools/tests/unit/src/serverless/flags.py` — comandos/flags nuevos.
- `devtools/tests/unit/src/serverless/packaging.py` — `build.zip`.
- `devtools/tests/conftest.py` — si referencia SAM o paths viejos.
- `devtools/tests/pytest.ini` — si la coleccion de tests necesita
  ajuste por las rutas nuevas.
- `serverless/lambda/services/*/tests/conftest.py` y `_helpers.py` /
  `_fixtures/` — solo si referencian SAM (probable: ninguno).
- `serverless/lambda/shared/tests/` — solo si referencian SAM.

## Criterios de aceptacion

- **AC-8.1**: When se ejecuta `devtools/.venv/bin/python -m pytest
  devtools/tests/`, Then la suite completa pasa (0 fallos, 0 errores).
- **AC-8.2**: When se busca `sam_generate|template.yaml|aws-sam` en
  `devtools/tests/` y `serverless/lambda/*/tests/`, Then no hay
  resultados.
- **AC-8.3**: When se ejecuta `serverless tests --type=coverage`, Then
  el coverage per-file de `devtools/serverless/` es >= 80%.
- **AC-8.4**: When se ejecutan los 4 `serverless tests --type=unit
  --lambda=<x>`, Then los 4 pasan.
- **AC-8.5**: When se ejecuta `serverless tests --type=unit --shared`,
  Then pasa.
- **AC-8.6**: When se ejecutan todos los comandos de B.1, Then ninguno
  retorna exit code != 0.
- **AC-8.7**: Given acceso a AWS dev, When se ejecuta la secuencia B.2
  completa, Then cada comando termina OK y `status` reporta el estado
  local consistente con AWS.
- **AC-8.8**: Given `deploy` ejecutado dos veces sin cambios, When la
  segunda corrida, Then reporta `NOOP` (idempotencia real verificada).
- **AC-8.9**: Given `destroy --yes` seguido de `provision-infra` +
  `deploy`, When termina, Then los 4 Lambdas responden a una invocacion
  (ciclo destruir/recrear verificado).

## Verificacion (Definition of Done de la fase)

```bash
# Parte A — refactor de tests
rg -l "sam_generate|template\.yaml|aws-sam|sam local|sam deploy" \
   devtools/tests/ serverless/lambda/*/tests/ serverless/lambda/shared/tests/
   # -> 0 resultados
devtools/.venv/bin/python -m pytest devtools/tests/ -v        # suite verde
python devtools/run.py serverless tests --type=coverage       # >= 80%

# Parte B — comandos reales
# (toda la bateria B.1 + B.2, ver arriba)
```

- [ ] AC-8.1..AC-8.9 cubiertos
- [ ] `sam_generate.py` (test) eliminado; cero referencias a SAM en tests
- [ ] Suite `devtools/tests/` 100% verde
- [ ] Coverage `devtools/serverless/` >= 80% per-file
- [ ] Los 4 `tests --lambda` + `tests --shared` verdes
- [ ] Todos los comandos B.1 pasan (exit 0)
- [ ] Todos los comandos B.2 pasan contra AWS dev (o documentados como
      pendientes en el PR si no hay acceso al momento)
- [ ] `destroy` + `provision-infra` + `deploy` reaprovisiona dev sin
      error

## Regla de cierre

Esta fase NO se marca como completa mientras quede un comando de B.1
fallando, un test rojo, o el coverage por debajo de 80%. La instruccion
es iterar — corregir, re-ejecutar, repetir — hasta que toda la bateria
pase. Solo entonces el PR esta listo para review.

---

[Anterior: 11](11-paralelizacion-worktrees.md) | [README](README.md)
