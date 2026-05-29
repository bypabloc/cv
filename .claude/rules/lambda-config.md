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
- **NUNCA** un eager import de una dep pesada (fido2/cryptography, argon2,
  pyotp) en el `__init__.py` de un subpaquete de `shared/`: usar PEP 562
  `__getattr__` (carga lazy). Ver `shared/auth/__init__.py` como referencia.

## Por que la memoria importa (memoria == CPU)

En Lambda la `memory` controla TAMBIEN la CPU asignada (proporcional).
128 MB ~= 0.07 vCPU. Por eso bajar memoria no solo arriesga OOM: ralentiza
el cold init Y el handler (cada request). El handler de un Lambda que toca
Neon/DynamoDB/SSM escala fuerte con la memoria (medido en auth: handler
~2.7s a 512 MB vs ~7.6s a 256 MB).

## Carga lazy: el fix de raiz del cold start

El cold start lo domina el TIEMPO DE IMPORTS. Importar una dep nativa
pesada (fido2 -> cryptography) cuesta segundos. Reglas:

- **Subir memoria NO arregla la causa** (solo compra CPU para importar mas
  rapido). La causa es importar lo que no se usa.
- El `__init__.py` de un subpaquete shared que re-exporta simbolos NO debe
  importar sus submodulos eager. Usar PEP 562 `__getattr__`: cada simbolo
  carga su submodulo on-demand. Asi `from shared.auth import verify_jwt`
  carga solo `jwt`, no `fido2`. Patron en `shared/auth/__init__.py`.
- Los controllers se importan DINAMICAMENTE por accion
  (`import_controller` -> `importlib.import_module('controllers.<op>.<act>')`).
  Combinado con el `__init__` lazy, una accion solo paga los submodulos que
  toca (ej. `login.start` no carga fido2).
- **NO** mover imports al `preload()` de cada controller: no evita el costo
  (importar cualquier cosa de `shared.auth` ejecuta su `__init__`), es
  churn en N controllers, y saca el import del snapshot de SnapStart (corre
  vivo en cada cold post-restore en vez de quedar snapshoteado). El fix
  correcto es el `__init__` lazy, dejando los imports en el top del modulo.
- Cada re-export lazy nuevo se cubre con un test que verifica que el
  import pesado NO se carga hasta acceder su simbolo (ver
  `shared/tests/unit/shared/auth/test_lazy_no_eager_fido2.py`).

## Minimos medidos actuales (dev, 2026-05)

| Lambda | memory | timeout | Razon medida |
|--------|--------|---------|--------------|
| `auth` | 512 | 30 | handler Neon (audit/JWT) ~2.7s; 256 MB daba ~7.6s |
| `users` | 512 | 30 | misma familia que auth (shared.auth + Neon) |
| `contact_form` | 384 | 30 | submit interactivo; cold restore ~5.5s; Turnstile HTTP + DDB + SQS |
| `tracking_pixel` | 256 | 30 | fire-and-forget (sendBeacon async, sin SnapStart); cold ~10s oculto al usuario, < timeout |
| `cv` | 512 | 30 | read-only Neon |

Los workers async (`*_worker`, `stream_processor`) y la Lambda `db` se
dimensionan por su carga propia (batch SQS / migraciones), no por esta
tabla.

## Como medir el minimo

1. Deployar el Lambda (con la carga lazy ya aplicada).
2. Probar memorias decrecientes sobre `$LATEST` (sin SnapStart = peor caso
   cold), invocando la accion mas pesada del Lambda:

```bash
for mem in 1024 512 384 256; do
  aws lambda update-function-configuration --function-name <fn> \
    --memory-size $mem --region us-east-1 --profile tfs-dev >/dev/null
  aws lambda wait function-updated --function-name <fn> \
    --region us-east-1 --profile tfs-dev
  aws lambda invoke --function-name <fn> --payload fileb://<event>.json \
    --log-type Tail --region us-east-1 --profile tfs-dev /tmp/out.json \
    --query 'LogResult' --output text | base64 -d \
    | grep -E 'Init Duration|^REPORT.*Duration'
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
| eager `from shared.x.heavy import ...` en `__init__` | Toda accion paga el import aunque no lo use | PEP 562 `__getattr__` lazy |
| Mover imports al `preload()` de cada controller | No evita el costo + churn + pelea con SnapStart | `__init__` lazy, imports en el top |
| Setear 128 MB "porque es el default" | El footprint base ya supera 128 MB -> OOM/lento | Medir; minimo real >= 256 MB |
| Subir memoria sin justificar en el manifest | Se pierde el por que; vuelve el over-provisioning | Comentario con la medicion |

## Referencias cruzadas

- `.claude/rules/lambda-controller.md` — formato general de los Lambdas.
- `.claude/rules/lambda-shared-imports.md` — portadores shared (donde
  vive cada dep pesada que conviene cargar lazy).
- `.claude/rules/verify-before-done.md` — medir antes de declarar listo.
- `shared/auth/__init__.py` — implementacion de referencia del lazy PEP 562.
