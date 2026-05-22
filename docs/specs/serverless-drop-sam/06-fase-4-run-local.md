# 06 — Fase 4: `run-local` sin SAM (`local_runtime.py`)

> [Anterior: 05](05-fase-3-provisioner-infra.md) | [README](README.md) | [Siguiente: 07](07-fase-5-integracion-cli.md)

Reemplazo de `sam local invoke`. Es la unica dependencia FUNCIONAL dura
de SAM (las demas eran azucar sobre AWS CLI / CloudFormation). Depende de
`packaging.py` y `vendoring.py`, NO de `provisioner.py` ni de Fase 1 —
por eso es paralelizable.

## Objetivo

`run --stage=local` hoy corre `sam local invoke`
([lambda_controller.py:135-177](../../../devtools/serverless/lambda_controller.py#L135-L177)),
que levanta un contenedor Docker con el runtime de AWS Lambda. Se
reemplaza por dos modos, en orden de preferencia:

1. **Modo RIE (recomendado, default)** — AWS Lambda Runtime Interface
   Emulator. Es el MISMO emulador que SAM usa por debajo, pero invocado
   directo via Docker, sin SAM. Imagen base oficial
   `public.ecr.aws/lambda/python:3.13`. Da un entorno identico al
   runtime AWS real.
2. **Modo directo (fallback, sin Docker)** — importa el handler en el
   `.venv` del backend y lo invoca con el event. Mas rapido, sin Docker,
   pero NO replica el sandbox de Lambda (filesystem read-only, limites
   de memoria). Util para iterar logica rapido.

El modo se elige con `--runtime-mode=rie|direct` (default `rie`; si
Docker no esta disponible, cae a `direct` con un `[WARN]`).

## Archivos afectados

### Crear

- `devtools/serverless/local_runtime.py` — los dos modos de ejecucion
  local.
- `devtools/tests/unit/src/serverless/test_local_runtime.py` — tests.

### Modificar

- `devtools/serverless/lambda_controller.py` — `_run_local` delega a
  `local_runtime` en vez de `sam local invoke`. Se elimina el
  `_ensure_tool('sam', ...)`.
- `devtools/serverless/flags.py` — agregar flag `--runtime-mode`; quitar
  `--debug` (era de `sam local invoke`).

## Modo RIE — diseno

```text
run --lambda=contact-form --stage=local --event=events/create.json
  |
  v
1. packaging.package_lambda(root, runtime)  -> build/ (deps + core/ + shared/)
2. docker run --rm
     -v <build>:/var/task:ro
     -p 9000:8080
     --env-file <env vars del stage dev renderizadas>
     public.ecr.aws/lambda/python:3.13
     core.handler.lambda_handler
   (el contenedor expone el RIE en :9000)
3. curl -s -d @<event.json>
     http://localhost:9000/2015-03-31/functions/function/invocations
4. imprime la respuesta JSON, baja el contenedor
```

El RIE viene incluido en la imagen base `public.ecr.aws/lambda/python`.
No hay que instalar nada extra mas alla de Docker (que el proyecto ya
usa para el stack Astro).

## Modo directo — diseno

```text
run --lambda=contact-form --stage=local --event=... --runtime-mode=direct
  |
  v
1. vendoring.vendored_shared(root)  -> core/shared/ poblado
2. sys.path.insert(0, root)
3. importlib: from core.handler import lambda_handler
4. event = json.load(event.json)
5. result = lambda_handler(event, _FakeContext())
6. imprime result; limpia el vendoring
```

`_FakeContext` minimo: `function_name`, `memory_limit_in_mb`,
`aws_request_id`, `get_remaining_time_in_millis()`.

## API publica de `local_runtime.py`

```python
class RuntimeMode(str, Enum):
    RIE = 'rie'
    DIRECT = 'direct'

def run_local(
    resolved: ResolvedLambda,
    *,
    event_path: Path | None,
    mode: RuntimeMode,
) -> int:
    """Ejecuta el lambda en local. Devuelve exit code.

    mode=RIE    -> Docker + RIE de la imagen base oficial.
    mode=DIRECT -> import del handler en el proceso actual.
    Si mode=RIE y Docker no esta -> cae a DIRECT con [WARN].
    """
```

## Por que RIE y no otra cosa

- Es lo que SAM usa internamente. Cero perdida de fidelidad respecto a
  `sam local invoke`.
- Imagen oficial mantenida por AWS, versionada por runtime.
- No agrega dependencias: Docker ya esta en el proyecto.
- El modo `direct` cubre el caso "no quiero levantar Docker para probar
  un cambio de logica".

## Criterios de aceptacion

- **AC-4.1**: Given un Lambda y un event JSON, When `run_local` con
  `mode=DIRECT`, Then el handler se ejecuta y la respuesta se imprime,
  sin Docker y sin SAM.
- **AC-4.2**: Given `mode=RIE` y Docker disponible, When `run_local`,
  Then se levanta el contenedor con la imagen
  `public.ecr.aws/lambda/python:<runtime>` y se invoca via el endpoint
  RIE.
- **AC-4.3**: Given `mode=RIE` y Docker NO disponible, When `run_local`,
  Then cae a `mode=DIRECT` con un `[WARN]` y NO falla.
- **AC-4.4**: Given un event JSON inexistente, When `run_local`, Then
  retorna exit code != 0 con un mensaje claro.
- **AC-4.5**: When se busca `sam local` en `devtools/serverless/`, Then
  no hay resultados.

## Tests requeridos

`test_local_runtime.py`:

- `test_run_local_direct_invokes_handler` [AC-4.1] — handler de prueba
  importable, sin Docker.
- `test_run_local_rie_builds_docker_command` [AC-4.2] —
  `subprocess.run` mockeado, verifica el comando docker.
- `test_run_local_rie_falls_back_to_direct_when_no_docker` [AC-4.3] —
  `shutil.which('docker')` mockeado a None.
- `test_run_local_when_event_missing_returns_error` [AC-4.4]
- `test_fake_context_has_required_attributes`

## Verificacion incremental con comandos devtools

Esta fase habilita `run --stage=local` sin SAM. Es ejecutable sin AWS
(modo directo) y con Docker (modo RIE). Se prueba contra los 4 lambdas:

```bash
# Modo directo — sin Docker, sin AWS: ejecuta el handler en el .venv
for L in contact-form tracking-pixel stream-processor db; do
  python devtools/run.py serverless run --lambda=$L --stage=local \
    --event=events/<evento>.json --runtime-mode=direct
done

# Modo RIE — requiere Docker: contenedor con la imagen base oficial
python devtools/run.py serverless run --lambda=contact-form --stage=local \
  --event=events/create.json --runtime-mode=rie

# La suite sigue verde
python devtools/run.py serverless tests --type=unit
python devtools/run.py serverless help
```

`run --stage=local --runtime-mode=direct` es OBLIGATORIO en esta fase (no
necesita Docker ni AWS) y debe pasar para los 4 lambdas. El modo RIE se
verifica si hay Docker disponible. NO se cierra la fase sin que el modo
directo funcione contra los 4 servicios.

## Verificacion (Definition of Done de la fase)

```bash
devtools/.venv/bin/python -m pytest devtools/tests/unit/src/serverless/test_local_runtime.py -v
python devtools/run.py docker lint --module=devtools
devtools/.venv/bin/python -m mypy devtools/serverless/local_runtime.py
# comandos devtools (modo directo, sin Docker ni AWS):
python devtools/run.py serverless run --lambda=contact-form --stage=local \
  --event=events/create.json --runtime-mode=direct
# modo RIE (requiere Docker):
python devtools/run.py serverless run --lambda=contact-form --stage=local \
  --event=events/create.json --runtime-mode=rie
python devtools/run.py serverless tests --type=unit
```

- [ ] AC-4.1..AC-4.5 cubiertos
- [ ] Coverage >= 80% per-file en `local_runtime.py`
- [ ] `run --stage=local --runtime-mode=direct` pasa para los 4 lambdas
- [ ] `run --stage=local --runtime-mode=rie` verificado con Docker (o
      documentado pendiente)
- [ ] Ruff + mypy sin errores

---

[Anterior: 05](05-fase-3-provisioner-infra.md) | [README](README.md) | [Siguiente: 07](07-fase-5-integracion-cli.md)
