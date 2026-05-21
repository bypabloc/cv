# Plan: Migracion del backend serverless a uv + subpaquetes shared/ con deps propias

> Migrar las 4 Lambdas Python de `pip` + `requirements.txt` a `uv` con un
> `pyproject.toml` + `uv.lock` por Lambda; reorganizar `serverless/shared/` en
> subpaquetes por dominio, cada uno con su propio `pyproject.toml` de deps;
> refactorizar todos los imports a la forma explicita `from shared.<subpaq>...`;
> y hacer que el vendoring de devtools resuelva por AST que subpaquetes (y
> deps) necesita cada Lambda. devtools arma el zip; SAM solo deploya.

## 1. Contexto / Problema

El backend serverless (`serverless/src/`) tiene 4 Lambdas Python 3.13
(`contact_form`, `tracking_pixel`, `db`, `stream_processor`). Hoy cada una
gestiona dependencias con `pip` via `requirements.txt` + `requirements-dev.txt`.
El tooling `devtools/` ya migro a `uv` (Python 3.14, `pyproject.toml` +
`uv.lock`, bootstrap automatico). El stack Python convive con dos gestores y
dos formatos de declaracion de dependencias.

Ademas, `serverless/shared/` (libreria comun vendorizada) tiene ~16 archivos
`.py` sueltos en su raiz mezclados con 4 subcarpetas ya agrupadas (`db/`,
`dynamodb/`, `cache/`, `rate_limit/`). El vendoring actual copia `shared/`
COMPLETO dentro de cada Lambda, asi que cada zip arrastra codigo (y deps) de
modulos que esa Lambda no usa.

Objetivos:

1. Unificar en `uv`, usar `pyproject.toml` (TOML estructurado, PEP 621) como
   unico formato y `uv.lock` como unica fuente de verdad de versiones.
   Eliminar todos los `requirements*.txt` versionados.
2. Reorganizar `serverless/shared/` para que NO haya archivos sueltos en la
   raiz: todo agrupado en subpaquetes por dominio, cada uno con su
   `pyproject.toml` declarando sus deps externas e internas.
3. Refactorizar TODOS los imports de las Lambdas (y de `shared/` internos) para
   que especifiquen el subpaquete: `from shared.observability.logger import ...`
   en vez de `from shared.logger import ...`.
4. Hacer que el vendoring de devtools escanee el AST de cada Lambda, detecte que
   subpaquetes de `shared/` usa (transitivamente), vendorice SOLO esos y sume
   al zip solo las deps de los `pyproject.toml` de esos subpaquetes.

### Hallazgos de exploracion

- `serverless/pyproject.toml` YA existe con PEP 621 `[project]` +
  `[dependency-groups]` pero SIN `[tool.uv]` ni `uv.lock` — sigue en pip.
- Cada Lambda tiene `requirements.txt` + `requirements-dev.txt` + `lambda.yaml`
  + `pytest.ini`.
- `serverless/shared/` raiz tiene 16 `.py` sueltos: `config.py`, `cors.py`,
  `dynamodb_client.py`, `exceptions.py`, `ip_extractor.py`, `logger.py`,
  `metrics.py`, `responses.py`, `ses_client.py`, `ssm_client.py`, `tracer.py`,
  `turnstile.py`, `types.py`, `ulid.py`, `validators.py`, `__init__.py`. Mas 4
  subcarpetas ya agrupadas: `db/`, `dynamodb/`, `cache/`, `rate_limit/`.
- Grafo de deps internas de `shared/` (aristas A->B = A importa B):
  `responses -> cors, exceptions, types`; `turnstile -> exceptions, logger,
  ssm_client`; `dynamodb/base -> dynamodb_client`; `rate_limit/rules ->
  dynamodb_client, cache.decorator`; `rate_limit/buckets -> dynamodb_client`.
  `db/` no importa nada de la raiz de `shared/`.
- Cada Lambda usa un subconjunto distinto de `shared/`: `contact_form` usa
  casi todo; `tracking_pixel` no usa `turnstile`/`ses`/`db`; `db` solo usa
  `db/` + `logger` + `tracer`; `stream_processor` usa `db/` + `cache/` +
  `dynamodb_client` + `logger` + `tracer` (no usa `http`).
- `devtools/serverless/vendoring.py` copia `serverless/shared/` ->
  `<lambda>/core/shared/` completo. `sam_generate.py` arma `template.yaml`;
  `lambda_controller.py` corre `sam build --use-container` (pip) + `sam deploy`.
- CI no corre nada de serverless; los tests Python solo van en pre-push.

## 2. Solucion Propuesta

`uv` con un `pyproject.toml` + `uv.lock` por Lambda (uv workspace con raiz en
`serverless/`); `shared/` reorganizado en subpaquetes por dominio, cada uno con
su `pyproject.toml`; imports explicitos al subpaquete; vendoring selectivo por
AST scan. devtools arma el zip con `uv pip install --target`; SAM solo deploya.

### Decisiones clave

- **Decision 1: workspace uv con member por Lambda** — cada Lambda es un
  `[tool.uv]` workspace member con su `pyproject.toml` declarando SOLO sus deps
  reales. Un unico `uv.lock` en la raiz resuelve todo en conjunto (sin drift).
- **Decision 2: devtools arma el zip completo con uv, SAM solo deploya** —
  devtools corre `uv pip install --target build/`, copia `core/` + los
  subpaquetes de `shared/` vendorizados, arma `function.zip` y lo pasa a `sam
  deploy` como artefacto. Sin `BuildMethod: python-uv` (no verificado GA).
- **Decision 3: `pyproject.toml` reemplaza `requirements*.txt`** — se eliminan
  los 8 `requirements*.txt`. Runtime en `[project.dependencies]`, test en
  `[dependency-groups] dev`. `uv.lock` raiz versionado; cualquier
  `requirements.txt` generado es efimero/gitignored.
- **Decision 4: dev deps de test centralizadas en la raiz** — `pytest`,
  `pytest-cov`, `pytest-mock`, `moto` en `[dependency-groups] dev` del
  `pyproject.toml` raiz. `pytest` corre desde `serverless/` con el `.venv` del
  workspace. Los `pytest.ini` por Lambda se absorben en
  `[tool.pytest.ini_options]` del raiz y se eliminan.
- **Decision 5: `shared/` SIN archivos sueltos, todo en subpaquetes por
  dominio** — la raiz de `shared/` queda solo con `__init__.py`. Los 16 sueltos
  se agrupan en 4 subpaquetes nuevos:
  - `core/` — `config.py`, `exceptions.py`, `types.py`, `ulid.py`
  - `aws/` — `dynamodb.py` (ex `dynamodb_client.py`), `ses.py` (ex
    `ses_client.py`), `ssm.py` (ex `ssm_client.py`)
  - `observability/` — `logger.py`, `tracer.py`, `metrics.py`
  - `http/` — `cors.py`, `responses.py`, `ip_extractor.py`, `turnstile.py`,
    `validators.py`
  Los 4 subpaquetes existentes (`db/`, `dynamodb/`, `cache/`, `rate_limit/`)
  se mantienen. Total: 8 subpaquetes, cero archivos sueltos.
- **Decision 6: cada subpaquete de `shared/` lleva su `pyproject.toml`** —
  PEP 621 minimo con `[project.dependencies]` declarando sus deps externas y
  sus deps internas a otros subpaquetes de `shared/`. Ejemplo:
  - `core/` -> `pydantic`, `pydantic-settings`
  - `aws/` -> `boto3`, `aws-lambda-powertools`
  - `observability/` -> `aws-lambda-powertools`
  - `http/` -> `httpx` + dep interna a `shared-core`, `shared-aws`,
    `shared-observability`
  - `db/` -> `sqlalchemy`, `psycopg[binary]`
  - `dynamodb/` -> `boto3`, `pydantic` + dep interna a `shared-aws`
  - `cache/` -> `boto3`
  - `rate_limit/` -> `boto3` + dep interna a `shared-aws`, `shared-cache`,
    `shared-core`
- **Decision 7: imports explicitos al subpaquete en TODO el codigo** — todos
  los `from shared import X` y `from shared.<modulo> import X` de las Lambdas y
  de los internos de `shared/` pasan a `from shared.<subpaquete>.<modulo>
  import X`. Se elimina (o se reduce a vacio) el re-export agregador de
  `shared/__init__.py`: ya no se importa "de shared" a secas. Dentro de un
  mismo subpaquete se permiten imports relativos (`from .cors import ...`).
- **Decision 8: vendoring selectivo por AST scan transitivo** — devtools
  escanea el AST de `core/**/*.py` de la Lambda, detecta los `from
  shared.<subpaquete>` usados, resuelve transitivamente las deps internas
  declaradas en los `pyproject.toml` de esos subpaquetes, vendoriza SOLO el
  conjunto cerrado de subpaquetes necesarios en `<lambda>/core/shared/<subpaq>`
  y suma al zip la union de deps externas de esos `pyproject.toml`. Si un
  subpaquete no es alcanzable desde la Lambda, ni su codigo ni sus deps entran
  al zip.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given el repo migrado, When se listan los archivos de `serverless/`,
  Then NO existe ningun `requirements.txt` ni `requirements-dev.txt` versionado.
- **AC-2**: Given cada Lambda en `serverless/src/<lambda>/`, When se inspecciona,
  Then tiene exactamente un `pyproject.toml` con `[project.dependencies]`
  declarando SOLO las deps que esa Lambda importa realmente.
- **AC-3**: Given `serverless/`, When se corre `uv lock`, Then se genera un
  unico `serverless/uv.lock` que resuelve las 4 Lambdas como workspace members
  sin conflicto de versiones.
- **AC-4**: Given `serverless/shared/`, When se lista su contenido, Then la raiz
  contiene SOLO `__init__.py` y carpetas — NO hay ningun otro archivo `.py`
  suelto.
- **AC-5**: Given cada subpaquete de `serverless/shared/` (los 4 nuevos + los 4
  existentes), When se inspecciona, Then tiene un `__init__.py` y un
  `pyproject.toml` que declara sus deps externas e internas.
- **AC-6**: Given el codigo de las 4 Lambdas, When se buscan imports de
  `shared`, Then todos tienen la forma `from shared.<subpaquete>...` — NO existe
  ningun `from shared import X` ni `from shared.<modulo>` directo a la raiz.
- **AC-7**: Given una Lambda, When devtools construye su zip, Then el AST scan
  detecta los subpaquetes de `shared/` usados, vendoriza SOLO ese conjunto
  cerrado (transitivo) y el zip contiene unicamente esos subpaquetes.
- **AC-8**: Given el Lambda `tracking_pixel` (no usa `http/turnstile` ni `db/`),
  When devtools arma su zip, Then el zip NO contiene `shared/http/turnstile.py`
  ni el subpaquete `shared/db/` ni la dep `httpx` ni `sqlalchemy`.
- **AC-9**: Given el Lambda `db`, When devtools arma su zip, Then el zip
  contiene `shared/db/`, `shared/observability/` y sus deps (`sqlalchemy`,
  `alembic`, `psycopg`, `aws-lambda-powertools`), y NO contiene `shared/http/`
  ni `httpx`.
- **AC-10**: Given una Lambda, When se ejecuta `python devtools/run.py
  serverless deploy --path=serverless/src/<lambda> --stage=dev`, Then devtools
  construye `function.zip` con `uv pip install --target` + `core/` +
  subpaquetes de `shared/` resueltos, y `sam deploy` sube ese artefacto sin
  correr `pip`.
- **AC-11**: Given una Lambda, When se ejecuta `serverless test-unit
  --path=serverless/src/<lambda>`, Then los tests corren con el `.venv` del
  workspace uv y pasan con coverage >= 80% (mismo resultado que pre-migracion).
- **AC-12**: Given el `db` Lambda deployado post-migracion, When se invoca
  `{"command": "current"}`, Then responde la revision Alembic correcta.
- **AC-13**: Given `.claude/rules/lambda-controller.md` y el scaffold
  `.claude/templates/lambda-controller/`, When se leen, Then describen
  `pyproject.toml` (no `requirements.txt`), la estructura de `shared/` en
  subpaquetes con `pyproject.toml`, y los imports explicitos `from
  shared.<subpaquete>`.

## 4. Diagrama de Flujo (Antes y Despues)

### Antes (pip + sam build + shared/ completo)

```
lambda.yaml ──> sam_generate ──> template.yaml (CodeUri: ., BuildMethod: python3.13)
                                       │
vendoring: copia shared/ COMPLETO ──> <lambda>/core/shared/
                                       │
                          sam build --use-container
                                       │
                          pip install -r requirements.txt
                                       │
                                       ▼
                          .aws-sam/build/<fn>.zip ──> sam deploy
                          (zip arrastra TODO shared/ + todas las deps)
```

### Despues (uv + devtools zip + vendoring selectivo por AST)

```
pyproject.toml (Lambda) + pyproject.toml (cada subpaquete shared/) + uv.lock
        │
        ▼
devtools build de <lambda>:
  1. AST scan de core/**/*.py ──> detecta {from shared.<subpaq>}
  2. resuelve transitivo: + subpaquetes que esos importan
       (lee dep internas de cada pyproject.toml de shared/)
  3. union de deps externas de los pyproject.toml de ese conjunto
  4. uv pip install --target build/ --no-dev   (solo esas deps)
  5. copia core/ ──> build/core/
  6. vendoriza SOLO los subpaquetes alcanzables ──> build/core/shared/<subpaq>
  7. zip -r function.zip build/
        │
        ▼
lambda.yaml ──> sam_generate ──> template.yaml (CodeUri: <function.zip>)
        │
        └──> sam deploy (sube el zip ya construido)
```

## 5. Diagrama ER

N/A — no hay cambios en base de datos. El schema de Neon y las migraciones
Alembic no se tocan; solo cambia el empaquetado y la organizacion del codigo.

## 6. Tests Requeridos

### 6.A. Verificacion de empaquetado y resolucion (devtools)

- WHEN se corre `uv lock` en `serverless/` THEN se genera un unico `uv.lock`
  con los 4 members resueltos sin error [AC-3]
- WHEN el AST scan corre sobre `tracking_pixel/core/` THEN el conjunto de
  subpaquetes resuelto NO incluye `http` (parcial: no `turnstile`) ni `db` [AC-8]
- WHEN devtools arma el zip de `tracking_pixel` THEN el zip NO contiene
  `shared/db/` ni `httpx` ni `sqlalchemy` [AC-8]
- WHEN devtools arma el zip de `db` THEN el zip contiene `shared/db/` +
  `sqlalchemy` + `alembic` + `psycopg` y NO contiene `shared/http/` ni `httpx`
  [AC-9]
- WHEN el AST scan encuentra `from shared.http.responses` (que importa
  `shared.core`) THEN el conjunto resuelto incluye transitivamente `core` [AC-7]

### 6.B. Unit tests del AST resolver (devtools/tests/)

- Path: `devtools/tests/serverless/test_vendoring_resolver_*.py` (nuevos)
- Property/parametrize: dado un set de imports `from shared.X`, el resolver
  devuelve el cierre transitivo correcto de subpaquetes
- Asserts EXACTOS (`== {'core', 'aws', 'http'}`), nunca `>=`
- Mockear: filesystem de `shared/` con fixtures; NO mockear el parser AST propio
- Verificacion: `python devtools/run.py test_runner --module=devtools --type=unit`

### 6.C. Unit tests de las Lambdas (pytest, existentes)

- Los tests ya existen en `serverless/src/<lambda>/tests/unit/`
- Tras el refactor de imports, los tests que importan `from shared...` deben
  actualizarse a la forma `from shared.<subpaquete>...`
- La suite completa de las 4 Lambdas pasa con coverage >= 80% per-file [AC-11]
- Verificacion: `python devtools/run.py serverless test-unit --path=<lambda>`

### 6.D. Typecheck

- `mypy` ya configurado en `[tool.mypy]` del raiz; debe seguir pasando tras
  mover los archivos de `shared/` y reescribir imports
- Verificacion: `mypy` desde `serverless/` con el `.venv` del workspace

### 6.E. E2E Tests

CONDICIONAL — tras migrar el Lambda `db`: deployar a `dev` y correr `serverless
db-current --stage=dev` para confirmar que el zip con `alembic` + subpaquetes
de `shared/` funciona en AWS real [AC-12]. No hay E2E de UI.

## 7. Archivos Afectados

### Crear

- `serverless/src/<lambda>/pyproject.toml` (x4) — PEP 621, workspace member,
  deps reales de cada Lambda.
  - Verificar: `uv lock` en `serverless/` resuelve sin error
- `serverless/uv.lock` — lockfile unico del workspace (generado, versionado).
  - Verificar: `uv sync --frozen` reproduce el `.venv` sin warnings
- `serverless/shared/core/` — subpaquete: `__init__.py`, `config.py`,
  `exceptions.py`, `types.py`, `ulid.py`, `pyproject.toml`.
  - Verificar: `python -c "import shared.core"` desde `serverless/`
- `serverless/shared/aws/` — subpaquete: `__init__.py`, `dynamodb.py`, `ses.py`,
  `ssm.py`, `pyproject.toml`.
  - Verificar: idem `import shared.aws`
- `serverless/shared/observability/` — subpaquete: `__init__.py`, `logger.py`,
  `tracer.py`, `metrics.py`, `pyproject.toml`.
  - Verificar: idem `import shared.observability`
- `serverless/shared/http/` — subpaquete: `__init__.py`, `cors.py`,
  `responses.py`, `ip_extractor.py`, `turnstile.py`, `validators.py`,
  `pyproject.toml`.
  - Verificar: idem `import shared.http`
- `serverless/shared/db/pyproject.toml` — deps del subpaquete db (existente).
- `serverless/shared/dynamodb/pyproject.toml` — deps del subpaquete dynamodb.
- `serverless/shared/cache/pyproject.toml` — deps del subpaquete cache.
- `serverless/shared/rate_limit/pyproject.toml` — deps del subpaquete rate_limit.
  - Verificar (los 4): `uv lock` resuelve incluyendo estos pyproject
- `devtools/serverless/shared_resolver.py` — modulo nuevo: AST scan de `core/`
  de una Lambda + resolucion transitiva del cierre de subpaquetes de `shared/`
  + union de deps externas.
  - Verificar: `devtools/tests/serverless/test_vendoring_resolver_*.py` pasan

### Modificar

- `serverless/pyproject.toml` — agregar `[tool.uv]` con `workspace.members`,
  mantener `[dependency-groups] dev`, quitar la union de runtime de
  `[project.dependencies]`.
  - Verificar: `uv sync` desde `serverless/` crea `.venv`
- `serverless/shared/__init__.py` — vaciar el re-export agregador (ya no se
  importa "de shared" a secas). Dejarlo vacio o con docstring.
  - Verificar: ningun `from shared import` queda en el repo (grep)
- `serverless/shared/http/responses.py` — imports: `from .cors`, `from
  shared.core.exceptions`, `from shared.core.types`.
- `serverless/shared/http/turnstile.py` — imports: `from
  shared.observability.logger`, `from shared.aws.ssm`, `from
  shared.core.exceptions`.
- `serverless/shared/dynamodb/base.py` — import: `from shared.aws.dynamodb`.
- `serverless/shared/rate_limit/rules.py` — imports: `from shared.aws.dynamodb`,
  `from shared.cache.decorator`.
- `serverless/shared/rate_limit/buckets.py` — import: `from shared.aws.dynamodb`.
- `serverless/shared/rate_limit/auto_blacklist.py` — reemplazar `import boto3`
  directo por `from shared.aws.dynamodb import get_table` (reutiliza el
  singleton).
  - Verificar (los de shared/): `mypy` + tests de las Lambdas que los usan
- `serverless/src/<lambda>/core/**/*.py` (x4 Lambdas) — refactor de TODOS los
  imports `from shared...` a `from shared.<subpaquete>...`. Buscar/reemplazar
  guiado por la tabla del informe `explore_shared-imports-map.md` seccion 7c.
  - Verificar: grep de `from shared import` y `from shared.<modulo-raiz>`
    devuelve vacio; tests de cada Lambda pasan
- `serverless/src/<lambda>/tests/**/*.py` — actualizar imports de `shared` en
  los tests al nuevo path.
  - Verificar: `serverless test-unit --path=<lambda>` pasa
- `devtools/serverless/vendoring.py` — usar `shared_resolver.py`: en vez de
  copiar `shared/` completo, vendorizar solo el cierre de subpaquetes resuelto.
  - Verificar: `run-local` y `test-unit` siguen funcionando
- `devtools/serverless/lambda_controller.py` — reemplazar `sam build
  --use-container` por: resolver deps via `shared_resolver` + `uv pip install
  --target build/ --no-dev`, copiar `core/`, vendorizar subpaquetes resueltos,
  armar `function.zip`, pasarlo a `sam deploy`.
  - Verificar: `serverless deploy --path=<lambda> --stage=dev` deploya OK
- `devtools/serverless/sam_generate.py` — `CodeUri` apunta al artefacto
  pre-construido; sin `Metadata.BuildMethod` de pip.
  - Verificar: `serverless sam-generate --path=<lambda>` produce template
    valido (`cfn-lint` sin errores)
- `devtools/serverless/testing.py` — `pytest` corre con el `.venv` del
  workspace uv.
  - Verificar: `serverless test-unit --path=<lambda>` pasa
- `devtools/serverless/lifecycle.py` — `serverless init` corre `uv sync` en el
  workspace `serverless/`.
  - Verificar: `serverless init` crea `.venv` desde `uv.lock`
- `serverless/.gitignore` — agregar `requirements*.txt` (efimeros) y `build/`.
- `serverless/src/<lambda>/.gitignore` (x4) — agregar `build/`, `function.zip`,
  `requirements*.txt`.
  - Verificar: `git status` limpio tras un build
- `.claude/rules/lambda-controller.md` — actualizar "Estructura obligatoria"
  (`pyproject.toml` en vez de `requirements*.txt`), la seccion de la libreria
  comun vendorizada (subpaquetes con `pyproject.toml` propio, vendoring
  selectivo por AST), los imports `from shared.<subpaquete>`, y "Verificacion".
  - Verificar: `claude -p` segun `claude-config-testing.md` (5 angulos)
- `.claude/templates/lambda-controller/` — reemplazar `requirements.txt` del
  scaffold por `pyproject.toml`; documentar la estructura de `shared/`.
  - Verificar: copiar el scaffold + `uv lock` funciona
- `.claude/docs/lambda-controller/` — actualizar los capitulos que mencionan
  `requirements*.txt` y la estructura de `shared/`.
  - Verificar: grep de `requirements` en `.claude/docs/lambda-controller/` vacio
- `.claude/docs/serverless-backend/` — actualizar la descripcion de `shared/`
  (estructura en subpaquetes) y del flujo de deploy.
  - Verificar: lectura manual
- `CLAUDE.md` (raiz) — actualizar el arbol de conocimiento: `shared/` en
  subpaquetes, gestor `uv`, sin `pip`/`requirements.txt`.
  - Verificar: lectura manual

### Eliminar

- `serverless/src/contact_form/requirements.txt`
- `serverless/src/contact_form/requirements-dev.txt`
- `serverless/src/contact_form/pytest.ini`
- `serverless/src/tracking_pixel/requirements.txt`
- `serverless/src/tracking_pixel/requirements-dev.txt`
- `serverless/src/tracking_pixel/pytest.ini`
- `serverless/src/db/requirements.txt`
- `serverless/src/db/requirements-dev.txt`
- `serverless/src/db/pytest.ini`
- `serverless/src/stream_processor/requirements.txt`
- `serverless/src/stream_processor/requirements-dev.txt`
- `serverless/src/stream_processor/pytest.ini`
- Los 16 `.py` sueltos de `serverless/shared/` raiz se ELIMINAN de la raiz
  (se mueven a sus subpaquetes — `git mv`, no borrado destructivo).
  - Verificar (todos): `uv run pytest` desde `serverless/` recolecta los tests
    de las 4 Lambdas; `git status` no muestra archivos perdidos

## 8. Descomposicion para Paralelizacion

N/A — el plan es Large por volumen (~50 archivos), pero el grafo de dependencias
lo hace mayormente secuencial: la reorganizacion de `shared/` debe completarse y
verificarse antes de tocar los imports de las Lambdas, y el AST resolver debe
existir antes de migrar el empaquetado. Solo los 4 `git mv` de subpaquetes y los
8 `pyproject.toml` de subpaquetes son paralelizables entre si. La ejecucion se
hace por fases (seccion 9), no por agentes concurrentes.

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] `uv` disponible en PATH (`uv --version`)
- [ ] `sam` CLI disponible y version anotada (`sam --version`)
- [ ] `serverless/.venv` actual reproducible (se va a recrear)
- [ ] Branch de trabajo creada (`refactor/serverless-uv-shared` o similar)
- [ ] Confirmado el mapa de imports de `explore_shared-imports-map.md` contra
      el codigo actual antes de mover archivos

### Fases de implementacion

1. **Reorganizar `shared/` en subpaquetes** — `git mv` de los 16 sueltos a
   `core/`, `aws/`, `observability/`, `http/`; crear `__init__.py` de cada uno;
   reescribir los imports internos de `shared/` (responses, turnstile,
   dynamodb/base, rate_limit/*). Validar AC-4 + `import shared.<subpaq>` OK.
2. **`pyproject.toml` por subpaquete de `shared/`** — crear los 8 (4 nuevos + 4
   existentes) con sus deps externas e internas. Validar AC-5.
3. **Refactor de imports en las 4 Lambdas** — reescribir `core/**` y `tests/**`
   a `from shared.<subpaquete>...`; vaciar `shared/__init__.py`. Validar AC-6 +
   los tests siguen pasando con vendoring completo (aun el viejo).
4. **Workspace uv + pyproject por Lambda** — crear los 4 `pyproject.toml`,
   `[tool.uv] workspace` en el raiz, `uv lock`, `uv sync`. Validar AC-1,2,3.
5. **AST resolver + vendoring selectivo** — crear `shared_resolver.py` con
   tests; reescribir `vendoring.py` para vendorizar el cierre transitivo.
   Validar AC-7,8,9 + `run-local`/`test-unit`. Validar AC-11.
6. **Migrar el empaquetado (Lambda piloto `contact_form`)** — reescribir el
   build en `lambda_controller.py`, ajustar `sam_generate.py`, `deploy
   --stage=dev`. Validar AC-10.
7. **Extender a las 3 Lambdas restantes** — deploy real de `db` + `db-current`.
   Validar AC-12.
8. **Limpieza + docs** — eliminar `requirements*.txt` + `pytest.ini`, ajustar
   `.gitignore`, actualizar `lambda-controller.md`, scaffold, docs, `CLAUDE.md`.
   Validar AC-13.

### Definition of Done

- [ ] Los 8 `requirements*.txt` y 4 `pytest.ini` eliminados (AC-1)
- [ ] 4 `pyproject.toml` por Lambda + `serverless/uv.lock` versionados (AC-2,3)
- [ ] La raiz de `serverless/shared/` solo tiene `__init__.py` + carpetas (AC-4)
- [ ] Los 8 subpaquetes de `shared/` tienen `__init__.py` + `pyproject.toml`
      (AC-5)
- [ ] Cero `from shared import X` / `from shared.<modulo-raiz>` en el repo (AC-6)
- [ ] El vendoring resuelve por AST el cierre transitivo correcto (AC-7)
- [ ] El zip de `tracking_pixel` no trae `db/` ni `httpx`/`sqlalchemy` (AC-8)
- [ ] El zip de `db` trae `db/` + `sqlalchemy`/`alembic`/`psycopg`, sin `http/`
      ni `httpx` (AC-9)
- [ ] `serverless deploy --stage=dev` funciona para las 4 Lambdas, zip armado
      por devtools, `sam deploy` sin `pip` (AC-10)
- [ ] `serverless test-unit` pasa para las 4 con coverage >= 80% (AC-11)
- [ ] `db` deployado en dev responde `db-current` correctamente (AC-12)
- [ ] `mypy` pasa desde `serverless/`
- [ ] devtools tests propios pasan, incluido el resolver nuevo
      (`test_runner --module=devtools --type=unit`)
- [ ] `.claude/rules/lambda-controller.md` + scaffold + docs + `CLAUDE.md`
      actualizados, validados con `claude -p` (AC-13)
- [ ] `git status` limpio (sin artefactos de build trackeados)
