# Configuracion de Lambdas: memoria minima 1024 MB + timeout

> TODOS los AWS Lambda del backend declaran `memory: 1024` como MINIMO en
> su `manifest.yaml` (politica del proyecto, decision del dueno
> 2026-06-10: memoria == CPU, se prioriza la latencia warm/cold; el free
> tier de GB-s cubre el trafico del portfolio). Las mediciones de minimos
> previas (128/256/512) quedan OBSOLETAS como justificacion del valor.
> El cold start se sigue atacando de raiz con imports lazy (subir memoria
> no reemplaza cortar imports). Aplica a
> `serverless/lambda/services/*/manifest.yaml`.

## Activacion

Aplica SIEMPRE que se:

- Cree o edite un `manifest.yaml` de un Lambda (campos `memory`/`timeout`).
- Ajuste `memory` o `timeout` de cualquier Lambda del backend.
- Diagnostique un `502` / "Task timed out" / cold start lento.
- Agregue una dependencia pesada (fido2/cryptography, argon2, sqlalchemy,
  ...) a un subpaquete de `serverless/lambda/shared/`.

NO aplica al frontend Astro ni a las apps de Cloudflare Pages.

## Reglas duras (SIEMPRE / NUNCA)

- **SIEMPRE** `memory: 1024` MINIMO en TODO `manifest.yaml` de
  `serverless/lambda/services/*/`. Es el piso del proyecto: NINGUN Lambda
  declara menos, aunque una medicion muestre que "cabe" en menos.
- **SIEMPRE** un Lambda nuevo nace con `memory: 1024`. El comentario del
  manifest referencia esta politica (no exige medicion para el piso).
- El piso tambien es el DEFAULT en codigo: si un manifest omite `memory`,
  devtools resuelve 1024 (`serverless/resolve.py` `_MANIFEST_DEFAULTS` +
  `provisioner.py`). Aun asi, los manifests lo declaran explicito.
- **SIEMPRE** que se quiera MAS de 1024, justificarlo en el comentario del
  manifest con una medicion real (OOM o latencia medida a 1024).
- **SIEMPRE** el `timeout` cubre el cold SIN SnapStart restore — el restore
  NO esta garantizado (ventana de optimizacion post-deploy, escalado,
  Lambdas sin SnapStart). Valores actuales del backend: 30-60 segun Lambda.
- **SIEMPRE** ante un cold start lento, la PRIMERA palanca sigue siendo
  **cortar imports** (carga lazy): el piso de memoria compra CPU, pero no
  elimina el costo de importar lo que no se usa.
- **NUNCA** bajar `memory` por debajo de 1024 — ni "porque la medicion
  dice que entra en 256", ni para ahorrar: la politica del piso pesa mas
  que el minimo medido.
- **NUNCA** un re-export en el `__init__.py` de un subpaquete de `shared/`
  (deben estar VACIOS): un re-export eager de una dep pesada (fido2/
  cryptography, argon2, pyotp) la arrastra en toda accion. Importar del
  modulo concreto (`from shared.auth.webauthn import ...`). Lo enforza
  `serverless lint-deps`. Ver `.claude/rules/lambda-shared-imports.md`.

## Por que el piso es 1024 (memoria == CPU)

En Lambda la `memory` controla TAMBIEN la CPU asignada (proporcional).
128 MB ~= 0.07 vCPU; 1024 MB ~= 0.57 vCPU. Bajar memoria no solo arriesga
OOM: ralentiza el cold init Y el handler (cada request). Medido en auth:
handler ~2.7s a 512 MB vs ~7.6s a 256 MB. Con el piso de 1024 todos los
Lambdas operan con ~4x la CPU de los viejos minimos de 256 — la latencia
manda sobre el costo (el free tier de 400k GB-s/mes cubre con holgura el
trafico del portfolio).

## Imports concretos: el fix de raiz del cold start

El cold start lo domina el TIEMPO DE IMPORTS. Importar una dep nativa
pesada (fido2 -> cryptography) cuesta segundos. Reglas:

- **Subir memoria NO arregla la causa** (solo compra CPU para importar mas
  rapido). La causa es importar lo que no se usa.
- Los `__init__.py` de `shared/*` estan VACIOS (cero re-exports). Se importa
  SIEMPRE del modulo concreto: `from shared.auth.jwt import verify_jwt`
  carga solo `jwt`, NUNCA `fido2`. Esto es inherentemente lazy y lo enforza
  `serverless lint-deps` (check no-submodule). Ver
  `.claude/rules/lambda-shared-imports.md`.
- Los controllers se importan DINAMICAMENTE por accion
  (`import_controller` -> `importlib.import_module('controllers.<op>.<act>')`).
  Combinado con los imports concretos, una accion solo paga los submodulos
  que toca (ej. `login.start` no carga fido2).
- **NO** mover imports al `preload()` de cada controller: es churn en N
  controllers y saca el import del snapshot de SnapStart. El fix correcto
  son los imports concretos, dejando los imports en el top del modulo.
- Los modelos SQLAlchemy se importan del MODULO CONCRETO
  (`from shared.db.models.auth.user import AuthUser`), NUNCA de un barrel:
  los `__init__.py` de dominio estan VACIOS (sin re-exports), igual que el
  resto de `shared/`. `registry.py` importa TODOS los modulos concretos —
  lo usan solo Alembic/seed (schema completo). Importar un modulo paga solo
  su closure (ej. `auth.audit_log` carga 7 tablas, no las 43).
- **FK targets por modulo**: si una tabla tiene una `ForeignKey()` a una
  tabla de OTRO modulo (intra o cross-domain), ese modulo concreto DEBE
  importarse o la FK no resuelve en INSERT/UPDATE (`NoReferencedTableError`
  -> 500). Cada modulo importa sus FK-targets: `auth/user.py` importa
  `cv/profile.py` (`auth_users.profile_id -> cv_profiles.id`),
  los modulos `cv/*` importan `taxonomy/catalog.py`,
  `visitor/tracking.py` importa `taxonomy/event_type.py`. Un SELECT no
  resuelve la FK (por eso `login.start` 404 no fallaba), pero un INSERT si:
  el bug de PR #199/#200 fue esto (register/login/users 500; el entonces
  `tracking_worker` —ya eliminado con SQS— terminaba a DLQ). Lo enforza el guard
  `shared/tests/unit/shared/db/test_model_module_load_resolves_foreign_keys.py`
  (importa cada modulo aislado y resuelve sus FK) + el Check 4 de
  `serverless lint-deps` (`__init__.py` vacios, sin barrels).
- Que NO se carga fido2 al importar jwt se cubre con un test en subproceso
  (`shared/tests/unit/shared/auth/test_lazy_no_eager_fido2.py`).

## Warmup en INIT (SnapStart)

Los lambdas Neon precalientan el trabajo CPU caro en el module-scope del
handler (INIT) para que quede en el SNAPSHOT de SnapStart y NO se pague en
cada cold/restore:

```python
import shared.db.models.auth  # noqa: F401 -- registra el dominio
from shared.db.warmup import warm_db

warm_db()  # engine (NullPool, sin conexion) + configure_mappers (best-effort)
```

`warm_db()` es best-effort (try/except): NUNCA rompe el INIT (ej. sin
DATABASE_URL en un test). NullPool no abre conexion en el INIT (las
conexiones no sobreviven al snapshot).

Los lambdas que NO usan Neon pero SI DynamoDB (ej. `tracking_pixel`
async) tienen el mismo problema con **boto3**: el cliente low-level
(`get_resource().meta.client`) y CADA modelo de operacion (`get_item`,
`query`, `update_item`, `invoke`) se construyen LAZY en la PRIMERA
llamada. A 128 MB (~0.07 vCPU) eso cae en EXECUTE y tarda segundos ->
puede agotar el timeout (sintoma: el log llega a "Starting execute phase"
y se cuelga 30s -> 502/504, con `Max Memory` al borde de 128). El fix
(NUNCA subir memoria) es warmear en INIT:

```python
from shared.aws.warmup import warm_aws_clients

# tracking_pixel ya no usa SQS: persiste el tracking invocando
# tracking_writer async (InvocationType='Event'), por eso warmea el
# cliente `lambda` ademas de dynamodb.
warm_aws_clients(dynamodb=True, lambda_=True)  # materializa .meta.client
# + ejercitar el read-path idempotente (NO writes) para construir los
#   modelos get_item/query en el snapshot:
get_ip_rule('0.0.0.0'); get_endpoint_rule('/track')
get_effective_count(ip='0.0.0.0', endpoint='/track', window_seconds=60)
```

`warm_aws_clients` es best-effort igual que `warm_db`. Construir el
cliente NO basta: hay que ejercitar las OPERACIONES reales que el EXECUTE
usara, porque boto3 las modela por-operacion bajo demanda.

## Config actual: 1024/30 uniforme en los 10 Lambdas

Desde 2026-06-10 los 10 Lambdas (`analytics`, `auth`, `contact_form`,
`cv`, `cv_admin`, `db`, `send_email`, `tracking_pixel`,
`tracking_writer`, `users`) declaran `memory: 1024` (piso uniforme) con
`timeout` 30-60 segun Lambda.

Historia (solo contexto, NO usar como justificacion para bajar): entre
2026-05 y 2026-06 se midieron minimos por Lambda (128-512 MB segun
footprint: fido2/argon2 en auth/users, sqlalchemy+psycopg en los Neon,
boto3 en los async). Esa practica se reemplazo por el piso uniforme de
1024: menos config divergente, ~4x CPU para cold y handler, y el costo
sigue dentro del free tier. Las observaciones tecnicas siguen validas
(footprint Neon ~117-214 MB; memoria==CPU; el warmup en INIT y los
imports lazy son lo que evita los timeouts, no la memoria).

Los lambdas async-target (`send_email`, `tracking_writer`) se invocan via
`invoke` Lambda->Lambda con `InvocationType='Event'` (NUNCA SQS). La
Lambda `db` se dimensiona por las migraciones; con el piso de 1024 ya no
requiere ajuste propio.

## X-Ray: NO se usa en este backend

- **NUNCA** agregar `aws-xray-sdk` ni `aws-lambda-powertools[all]` (el extra
  `[all]` arrastra `aws-xray-sdk`). Usar `aws-lambda-powertools` sin extras.
- **NUNCA** instanciar un `Tracer` de Powertools ni decorar con
  `@tracer.capture_lambda_handler`. El provisioner deploya con
  `--tracing-config Mode=PassThrough` (no instrumenta).
- Si en el futuro se quiere tracing, es una decision explicita: re-evaluar
  costo ($ por traza) + el import en el cold start.

## Como medir (solo para subir POR ENCIMA del piso o diagnosticar)

La medicion ya NO se usa para elegir el valor base (es 1024 fijo). Se usa
para: (a) justificar MAS de 1024 (OOM o latencia inaceptable medida), o
(b) diagnosticar un 502/timeout. Sin tocar la funcion, la via preferida
son los REPORT de CloudWatch de invocaciones reales:

```bash
aws logs filter-log-events --log-group-name /aws/lambda/<fn> \
  --start-time $(( ($(date +%s) - 21600) * 1000 )) \
  --filter-pattern 'REPORT' --region us-east-1 --profile tfs-dev \
  --query 'events[].message' --output text | tr '\t' '\n' \
  | rg -o 'Init Duration: [0-9.]+ ms|Max Memory Used: [0-9]+ MB|Duration: [0-9.]+ ms'
```

Si `Max Memory Used` se acerca al limite o el handler queda CPU-bound,
subir el manifest por ENCIMA de 1024 documentando la medicion en el
comentario. `serverless deploy` reconcilia `$LATEST` al manifest.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| `memory` < 1024 en un manifest ("la medicion dice que cabe en 256") | Viola el piso del proyecto; CPU-starved en cold y handler | `memory: 1024` minimo, sin excepcion |
| Lambda nuevo con el default de AWS (128) o con un minimo medido | El piso es politica, no medicion | Nace con `memory: 1024` |
| Confiar en el piso de memoria para "arreglar" un cold start de imports | 4x CPU acelera, pero el costo de importar lo que no se usa sigue | Cortar imports (lazy) + warmup en INIT |
| `timeout` ajustado al cold CON restore | El restore no esta garantizado -> 502 en la ventana post-deploy | timeout cubre el cold SIN restore |
| Re-export en `__init__` de `shared/*` (deben estar vacios) | Toda accion paga el import aunque no lo use | Importar del modulo concreto; lint-deps lo enforza |
| Mover imports al `preload()` de cada controller | No evita el costo + churn + pelea con SnapStart | Imports concretos en el top + warmup en INIT |
| Subir POR ENCIMA de 1024 sin medicion en el comentario | Se pierde el por que; over-provisioning sin control | Comentario con la medicion (REPORT reales) |

## Referencias cruzadas

- `.claude/rules/lambda-controller.md` — formato general de los Lambdas.
- `.claude/rules/lambda-shared-imports.md` — contrato de imports concretos
  por modulo (inits vacios) + el check no-submodule de `lint-deps`.
- `.claude/rules/verify-before-done.md` — medir antes de declarar listo.
- `shared/db/warmup.py` — `warm_db()` para el warmup de INIT (SnapStart).
