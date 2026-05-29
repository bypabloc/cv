# Refactor: shared sin barrels + cold start + 128 MB

> Eliminar los re-export eager de los `__init__.py` de `shared/` (init
> vacios, imports al modulo concreto), eliminar X-Ray, aislar models por
> dominio, sacar alembic del zip de los lambdas que no migran, SnapStart en
> todos moviendo el trabajo caro al INIT, y bajar la memoria de cada lambda
> a **128 MB** validando con medicion en dev.

## Contexto

El cold start de los Neon-lambdas lo domina el costo CPU de importar el
stack SQLAlchemy + boto3 + powertools (memoria == CPU). Causas:

1. Los `__init__.py` de `shared/*` hacen re-export **eager**: importar un
   simbolo del barrel arrastra TODO el subpaquete (`shared.aws` instancia
   un cliente SES module-scope aunque el lambda no mande email;
   `shared.db` arrastra **alembic** que solo usa el lambda `db`).
2. `shared.db.models.__init__` importa los 5 dominios -> auth registra las
   43 clases del schema cuando solo usa ~12 (`configure_mappers()` caro).
3. X-Ray (`aws-lambda-powertools[all]` -> `aws-xray-sdk`) se importa e
   instancia en todos los handlers; el usuario NO lo usa.

## Decisiones (no reabribles)

- **D1**: `__init__.py` de `shared/*` quedan **vacios** (docstring-only),
  cero re-exports. NO se eliminan (evita riesgo namespace-package con el
  vendoring + dual-copy en tests). Todos importan del modulo concreto:
  `from shared.aws.ssm import get_secret`.
- **D2**: se elimina el hack PEP 562 lazy de `shared/auth/__init__.py`
  (innecesario: el import directo ya es lazy).
- **D3**: un solo `Base.metadata` (Alembic lo necesita). Aislamiento por
  dominio = importar solo el submodulo del dominio. Confirmado: cero
  `relationship()` cross-domain -> los dominios son import-independientes.
- **D4**: Alembic se mueve a su propio subpaquete `shared/db_migrations/`
  (dep `alembic`), solo lo incluye el lambda `db`. Sale del zip de los
  otros 5.
- **D5**: X-Ray eliminado por completo (`[all]` -> sin extras, sin
  `tracer.py`, sin `@tracer`, sin `Mode=Active`). Documentado en la rule
  de aws.
- **D6**: SnapStart en TODOS los lambdas HTTP; el trabajo caro (engine +
  `configure_mappers()` + SSM warm) se mueve al module-scope del handler
  (INIT) para que quede en el snapshot.
- **D7**: memoria objetivo **128 MB** por lambda, validada con medicion
  real en dev. Donde un lambda no aguante, se documenta con datos.

## Orden de ejecucion (verde en cada commit)

1. **Fase 1 — X-Ray out**: powertools sin `[all]`, borrar `tracer.py` +
   los 9 `@tracer`, `Mode=Active` fuera del provisioner, rule aws.
2. **Fase 2 — consumidores a imports concretos**: reescribir los ~173
   `from shared.<pkg> import` -> `from shared.<pkg>.<modulo> import`. Los
   init siguen re-exportando (nada se rompe). Por servicio (file-exclusive).
3. **Fase 3 — providers lazy**: ses client lazy, alembic a
   `shared/db_migrations/`, models per-dominio (repos al submodulo).
4. **Fase 4 — vaciar inits**: con grep confirmando cero imports barrel,
   vaciar los `__init__.py` de `shared/*` + `models/*`. Borrar PEP 562.
5. **Fase 5 — SnapStart + INIT**: snap_start en tracking_pixel + cv;
   mover engine/configure_mappers/SSM al INIT de cada handler.
6. **Fase 6 — rules + validator**: reescribir lambda-shared-imports.md
   (contrato = import concreto, no barrel), lambda-config.md (128 MB),
   ajustar import_validator.py si exige barrel.
7. **Fase 7 — deploy dev + medir 128 MB**: bajar memoria, deploy, probar
   cada lambda, reportar numeros.

## Verificacion

```bash
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=unit --lambda=<X>
python devtools/run.py serverless lint-deps
```

Esta carpeta es efimera: se elimina al mergear a dev.
