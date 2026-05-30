# Configuracion de Lambdas: memoria/timeout minimos medidos

> Los AWS Lambda del backend usan la configuracion MINIMA que pasa los
> tests funcionales + cold start, justificada con una medicion en el
> comentario del manifest. NUNCA se sube memoria para enmascarar un cold
> start lento de imports: primero se corta el import (carga lazy). Aplica
> a `serverless/lambda/services/*/manifest.yaml`.

## Activacion

Aplica SIEMPRE que se:

- Cree o edite un `manifest.yaml` de un Lambda (campos `memory`/`timeout`).
- Ajuste `memory` o `timeout` de cualquier Lambda del backend.
- Diagnostique un `502` / "Task timed out" / cold start lento.
- Agregue una dependencia pesada (fido2/cryptography, argon2, sqlalchemy,
  ...) a un subpaquete de `serverless/lambda/shared/`.

NO aplica al frontend Astro ni a las apps de Cloudflare Pages.

## Reglas duras (SIEMPRE / NUNCA)

- **SIEMPRE** `memory`/`timeout` = el MINIMO medido que pasa los tests con
  latencia aceptable para el caso de uso del Lambda (interactivo vs
  fire-and-forget).
- **SIEMPRE** justificar el valor en el comentario del manifest con una
  medicion real (init / handler / cold observados + por que no menos).
- **SIEMPRE** el `timeout` cubre el cold SIN SnapStart restore — el restore
  NO esta garantizado (ventana de optimizacion post-deploy, escalado,
  Lambdas sin SnapStart). Default del backend: `30`.
- **SIEMPRE** ante un cold start lento, la PRIMERA palanca es **cortar
  imports** (carga lazy), NO subir memoria.
- **NUNCA** subir `memory`/`timeout` "por las dudas" ni para enmascarar el
  costo de imports. Eso es over-provisioning.
- **NUNCA** asumir que `128 MB` (el default de AWS) alcanza: el footprint
  base (Python + boto3 + pydantic + el cierre de `shared/`) ya supera
  ~118 MB. Hay que MEDIR; el minimo real de estos Lambdas es >= 256 MB.
- **NUNCA** un re-export en el `__init__.py` de un subpaquete de `shared/`
  (deben estar VACIOS): un re-export eager de una dep pesada (fido2/
  cryptography, argon2, pyotp) la arrastra en toda accion. Importar del
  modulo concreto (`from shared.auth.webauthn import ...`). Lo enforza
  `serverless lint-deps`. Ver `.claude/rules/lambda-shared-imports.md`.

## Por que la memoria importa (memoria == CPU)

En Lambda la `memory` controla TAMBIEN la CPU asignada (proporcional).
128 MB ~= 0.07 vCPU. Por eso bajar memoria no solo arriesga OOM: ralentiza
el cold init Y el handler (cada request). El handler de un Lambda que toca
Neon/DynamoDB/SSM escala fuerte con la memoria (medido en auth: handler
~2.7s a 512 MB vs ~7.6s a 256 MB).

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
  el bug de PR #199/#200 fue esto (register/login/users 500, tracking_worker
  a DLQ). Lo enforza el guard
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

Los lambdas que NO usan Neon pero SI DynamoDB/SQS (ej. `tracking_pixel`
async) tienen el mismo problema con **boto3**: el cliente low-level
(`get_resource().meta.client`) y CADA modelo de operacion (`get_item`,
`query`, `update_item`, `send_message`) se construyen LAZY en la PRIMERA
llamada. A 128 MB (~0.07 vCPU) eso cae en EXECUTE y tarda segundos ->
puede agotar el timeout (sintoma: el log llega a "Starting execute phase"
y se cuelga 30s -> 502/504, con `Max Memory` al borde de 128). El fix
(NUNCA subir memoria) es warmear en INIT:

```python
from shared.aws.warmup import warm_aws_clients

warm_aws_clients(dynamodb=True, sqs=True)  # materializa .meta.client
# + ejercitar el read-path idempotente (NO writes) para construir los
#   modelos get_item/query en el snapshot:
get_ip_rule('0.0.0.0'); get_endpoint_rule('/track')
get_effective_count(ip='0.0.0.0', endpoint='/track', window_seconds=60)
```

`warm_aws_clients` es best-effort igual que `warm_db`. Construir el
cliente NO basta: hay que ejercitar las OPERACIONES reales que el EXECUTE
usara, porque boto3 las modela por-operacion bajo demanda.

## Minimos medidos actuales (dev, 2026-05, cold `$LATEST` sin restore)

Medidos tras el refactor shared-no-barrels: lazy imports + X-Ray eliminado
+ models per-dominio + warmup en INIT (`shared.db.warmup.warm_db`).

| Lambda | memory | timeout | Razon medida |
|--------|--------|---------|--------------|
| `auth` | 256 | 30 | webauthn (fido2) a 128 MB: 127/128 MB (OOM inminente) + 21s CPU-starved ~ al borde del timeout. A 256 entra comodo (login 174 MB) |
| `users` | 256 | 30 | misma familia que auth; argon2id (password) es memory-hard |
| `cv` | 256 | 30 | read-only Neon usa 118-165 MB; a 128 quedan 10 MB headroom. Handler ~9s es Neon-I/O-bound (no escala con memoria) |
| `contact_form` | 256 | 30 | footprint Neon 117/128 MB a 128 (11 MB headroom); 157 MB a 256 |
| `tracking_pixel` | 128 | 30 | UNICO a 128: async (sin Neon -> sin sqlalchemy). Imports de Neon/ua_parser diferidos al path sync legacy (lazy) + warmup de los clientes boto3 y del read-path del rate-limit en INIT (`shared.aws.warmup.warm_aws_clients` + `get_ip/endpoint_rule`). Restore (SnapStart) ~1.16s, warm ~380ms, 111/128 MB (17 MB headroom). SIN warmup, boto3 construia los modelos de operacion (get_item/query) en EXECUTE a 0.07 vCPU -> >30s -> timeout 502/504 |

**El footprint base de un lambda Neon (sqlalchemy + pydantic + modelos +
clientes) es ~117-127 MB** -> 128 MB NO deja headroom seguro: el minimo
real de cualquier lambda que importe `shared.db`/sqlalchemy es **256 MB**.
Solo un lambda async sin Neon (como `tracking_pixel` en `ASYNC_MODE`) baja
a 128. Verificar SIEMPRE con la medicion de abajo, NUNCA asumir 128.

Los workers async (`*_worker`, `stream_processor`) y la Lambda `db` se
dimensionan por su carga propia (batch SQS / migraciones), no por esta
tabla.

## X-Ray: NO se usa en este backend

- **NUNCA** agregar `aws-xray-sdk` ni `aws-lambda-powertools[all]` (el extra
  `[all]` arrastra `aws-xray-sdk`). Usar `aws-lambda-powertools` sin extras.
- **NUNCA** instanciar un `Tracer` de Powertools ni decorar con
  `@tracer.capture_lambda_handler`. El provisioner deploya con
  `--tracing-config Mode=PassThrough` (no instrumenta).
- Si en el futuro se quiere tracing, es una decision explicita: re-evaluar
  costo ($ por traza) + el import en el cold start.

## Como medir el minimo

1. Deployar el Lambda (con la carga lazy ya aplicada).
2. Probar memorias decrecientes sobre `$LATEST` (sin SnapStart = peor caso
   cold), invocando la accion mas pesada del Lambda:

```bash
for mem in 512 256 128; do
  aws lambda update-function-configuration --function-name <fn> \
    --memory-size $mem --region us-east-1 --profile tfs-dev >/dev/null
  aws lambda wait function-updated --function-name <fn> \
    --region us-east-1 --profile tfs-dev
  aws lambda invoke --function-name <fn> --payload fileb://<event>.json \
    --log-type Tail --region us-east-1 --profile tfs-dev ./tmp/out.json \
    --query 'LogResult' --output text | base64 -d \
    | rg 'Init Duration|^REPORT.*Duration|Max Memory'
done
```

3. Elegir el MENOR `memory` donde: (a) no hay OOM, (b) el cold no-restore
   queda holgado bajo el `timeout`, (c) la latencia warm es aceptable para
   el caso de uso. Documentarlo en el comentario del manifest.
4. `serverless deploy` reconcilia `$LATEST` al manifest (descarta el drift
   de la medicion) y publica la version con SnapStart.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Subir a 1024 MB porque "daba 502" | Enmascara un cold start de imports; over-provisioning | Cortar imports (lazy) + medir el minimo |
| `timeout` ajustado al cold CON restore | El restore no esta garantizado -> 502 en la ventana post-deploy | timeout cubre el cold SIN restore |
| Re-export en `__init__` de `shared/*` (deben estar vacios) | Toda accion paga el import aunque no lo use | Importar del modulo concreto; lint-deps lo enforza |
| Mover imports al `preload()` de cada controller | No evita el costo + churn + pelea con SnapStart | Imports concretos en el top + warmup en INIT |
| Setear 128 MB "porque es el default" | El footprint base ya supera 128 MB -> OOM/lento | Medir; minimo real >= 256 MB |
| Subir memoria sin justificar en el manifest | Se pierde el por que; vuelve el over-provisioning | Comentario con la medicion |

## Referencias cruzadas

- `.claude/rules/lambda-controller.md` — formato general de los Lambdas.
- `.claude/rules/lambda-shared-imports.md` — contrato de imports concretos
  por modulo (inits vacios) + el check no-submodule de `lint-deps`.
- `.claude/rules/verify-before-done.md` — medir antes de declarar listo.
- `shared/db/warmup.py` — `warm_db()` para el warmup de INIT (SnapStart).
