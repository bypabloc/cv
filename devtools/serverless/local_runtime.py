"""Ejecucion local de un Lambda — reemplazo de `sam local invoke`.

`sam local invoke` era la unica dependencia FUNCIONAL dura de SAM: las
demas eran azucar sobre AWS CLI / CloudFormation. Este modulo la elimina
ofreciendo dos modos de ejecucion local, en orden de preferencia:

  1. **Modo RIE** (default) — AWS Lambda Runtime Interface Emulator. Es el
     MISMO emulador que SAM usa por debajo, invocado directo via Docker
     sobre la imagen oficial `public.ecr.aws/lambda/python:<runtime>`. Da
     un entorno identico al runtime AWS real, sin pasar por SAM.
  2. **Modo directo** (fallback) — importa `core.handler.lambda_handler`
     en el proceso de devtools y lo invoca con un `_FakeContext`. No
     replica el sandbox de Lambda (filesystem read-only, limites de
     memoria), pero es rapido y no necesita Docker. Util para iterar
     logica.

Si se pide modo RIE y Docker no esta disponible, se cae a modo directo
con un `[WARN]` — `run-local` nunca falla por ausencia de Docker.

El modo RIE necesita `packaging.package_lambda` (el `build/` con deps +
`core/` + `shared/`); el modo directo necesita `vendoring.vendored_shared`
(para que `import shared...` resuelva en el proceso). NO depende de
`provisioner.py` ni de la capa de estado.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any

from shared.console import CYAN
from shared.console import GREEN
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err

from serverless.packaging import PackagingError
from serverless.packaging import package_lambda
from serverless.resolve import ResolvedLambda
from serverless.vendoring import VendoringError
from serverless.vendoring import vendored_shared


# Imagen base oficial del runtime de AWS Lambda Python. Trae el RIE
# incluido; se versiona por runtime (`:3.13`).
_RIE_IMAGE_PREFIX = 'public.ecr.aws/lambda/python'

# Puerto del host mapeado al :8080 del RIE dentro del contenedor.
_RIE_HOST_PORT = 9000

# Endpoint que expone el RIE para invocar la funcion.
_RIE_INVOKE_PATH = '2015-03-31/functions/function/invocations'

# Segundos de espera a que el RIE levante antes de hacer el curl.
_RIE_STARTUP_WAIT = 2.0


class RuntimeMode(StrEnum):
    """Modo de ejecucion local de un Lambda.

    Members
    -------
    RIE
        Docker + AWS Lambda Runtime Interface Emulator (default).
    DIRECT
        Import del handler en el proceso de devtools (fallback).
    """

    RIE = 'rie'
    DIRECT = 'direct'


@dataclass
class _FakeContext:
    """Context minimo de AWS Lambda para el modo directo.

    Reproduce los atributos del objeto `context` que el runtime de AWS
    pasa al handler. Suficiente para que el handler corra en local sin el
    sandbox real.

    Attributes
    ----------
    function_name : str
        Nombre logico de la funcion.
    memory_limit_in_mb : int
        Limite de memoria declarado en el manifiesto.
    aws_request_id : str
        Identificador de la invocacion (sintetico en local).
    """

    function_name: str = 'local'
    memory_limit_in_mb: int = 256
    aws_request_id: str = 'local-invoke'

    def get_remaining_time_in_millis(self) -> int:
        """Milisegundos restantes de ejecucion (fijo en local)."""
        return 300_000


def _docker_available() -> bool:
    """True si el binario `docker` esta en el PATH."""
    return shutil.which('docker') is not None


def _load_event(event_path: Path | None) -> tuple[Any, str | None]:
    """Carga el event JSON desde disco.

    Parameters
    ----------
    event_path : Path | None
        Ruta al archivo de event, o None para usar `{}`.

    Returns
    -------
    tuple[Any, str | None]
        `(event, error)` — el event parseado y None si todo ok, o
        `({}, mensaje)` si el archivo no existe o el JSON es invalido.
    """
    if event_path is None:
        return {}, None
    if not event_path.is_file():
        return {}, f'Event JSON no existe: {event_path}'
    try:
        return json.loads(event_path.read_text(encoding='utf-8')), None
    except json.JSONDecodeError as exc:
        return {}, f'Event JSON invalido ({event_path}): {exc}'


def _run_direct(resolved: ResolvedLambda, event: Any) -> int:
    """Ejecuta el handler importandolo en el proceso de devtools.

    Vendoriza `shared/` en `core/shared/`, agrega la raiz del lambda al
    `sys.path`, importa `core.handler.lambda_handler` y lo invoca con un
    `_FakeContext`. Imprime el resultado como JSON.

    Parameters
    ----------
    resolved : ResolvedLambda
        Lambda objetivo ya resuelto.
    event : Any
        Event de entrada para el handler.

    Returns
    -------
    int
        0 si el handler corrio sin excepcion, 1 si fallo.
    """
    manifest = resolved.manifest
    context = _FakeContext(
        function_name=str(manifest.get('name', 'local')),
        memory_limit_in_mb=int(manifest.get('memory', 256)),
    )
    root = str(resolved.root)
    print(_c(CYAN, f'[direct] import core.handler desde {root}'))

    try:
        with vendored_shared(resolved.root):
            added_path = root not in sys.path
            if added_path:
                sys.path.insert(0, root)
            try:
                module = importlib.import_module('core.handler')
                module = importlib.reload(module)
                result = module.lambda_handler(event, context)
            finally:
                if added_path and root in sys.path:
                    sys.path.remove(root)
    except VendoringError as exc:
        _err(str(exc))
        return 1
    except Exception as exc:  # noqa: BLE001 - cualquier fallo del handler
        _err(f'El handler lanzo una excepcion: {exc}')
        return 1

    print(_c(GREEN, 'Respuesta del handler:'))
    print(json.dumps(result, indent=2, default=str))
    return 0


def _build_docker_command(
    build_path: Path,
    *,
    runtime: str,
    handler: str,
) -> list[str]:
    """Arma el comando `docker run` que levanta el RIE.

    Monta el `build/` del lambda en `/var/task` (read-only), publica el
    puerto del RIE y usa la imagen oficial del runtime.

    Parameters
    ----------
    build_path : Path
        Directorio del artefacto construido por `package_lambda`.
    runtime : str
        Runtime del manifiesto (`python3.13`); fija el tag de la imagen.
    handler : str
        Handler del manifiesto (`core.handler.lambda_handler`).

    Returns
    -------
    list[str]
        Comando `docker run` completo.
    """
    image_tag = runtime.removeprefix('python')
    return [
        'docker',
        'run',
        '--rm',
        '-v',
        f'{build_path}:/var/task:ro',
        '-p',
        f'{_RIE_HOST_PORT}:8080',
        f'{_RIE_IMAGE_PREFIX}:{image_tag}',
        handler,
    ]


def _invoke_rie_endpoint(event: Any) -> int:
    """Invoca el endpoint RIE del contenedor con `curl`.

    Parameters
    ----------
    event : Any
        Event de entrada, se envia como cuerpo de la peticion.

    Returns
    -------
    int
        Exit code del `curl`.
    """
    url = f'http://localhost:{_RIE_HOST_PORT}/{_RIE_INVOKE_PATH}'
    cmd = ['curl', '-s', '-d', json.dumps(event), url]
    print(_c(CYAN, f'$ {" ".join(cmd)}'))
    # S603: comando armado por devtools (binario fijo + URL del RIE),
    # sin input no confiable de usuario.
    result = subprocess.run(  # noqa: S603
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(_c(GREEN, 'Respuesta del RIE:'))
        print(result.stdout)
    return result.returncode


def _run_rie(resolved: ResolvedLambda, event: Any) -> int:
    """Ejecuta el lambda en un contenedor con el RIE oficial.

    Empaqueta el lambda con `package_lambda`, levanta el contenedor de la
    imagen base del runtime y lo invoca via el endpoint RIE.

    Parameters
    ----------
    resolved : ResolvedLambda
        Lambda objetivo ya resuelto.
    event : Any
        Event de entrada para la invocacion.

    Returns
    -------
    int
        0 si la invocacion termino bien, != 0 en caso de error.
    """
    manifest = resolved.manifest
    runtime = str(manifest['runtime'])
    handler = str(manifest['handler'])

    try:
        build_path, _closure, _deps = package_lambda(
            resolved.root,
            runtime=runtime,
        )
    except PackagingError as exc:
        _err(str(exc))
        return 1

    docker_cmd = _build_docker_command(
        build_path,
        runtime=runtime,
        handler=handler,
    )
    print(_c(CYAN, f'$ {" ".join(docker_cmd)}'))
    # S603: comando armado por devtools (binario fijo `docker` + flags
    # derivados del manifiesto), sin input no confiable de usuario.
    container = subprocess.Popen(  # noqa: S603
        docker_cmd,
    )
    try:
        time.sleep(_RIE_STARTUP_WAIT)
        return _invoke_rie_endpoint(event)
    finally:
        container.terminate()
        container.wait()


def run_local(
    resolved: ResolvedLambda,
    *,
    event_path: Path | None,
    mode: RuntimeMode,
) -> int:
    """Ejecuta el lambda en local. Devuelve el exit code.

    `mode=RIE` levanta un contenedor con la imagen oficial del runtime y
    el RIE de AWS. `mode=DIRECT` importa el handler en el proceso de
    devtools. Si se pide `mode=RIE` y Docker no esta disponible, se cae a
    `mode=DIRECT` con un `[WARN]` — `run-local` nunca falla por ausencia
    de Docker.

    Parameters
    ----------
    resolved : ResolvedLambda
        Lambda objetivo ya resuelto.
    event_path : Path | None
        Ruta al archivo de event JSON, o None para invocar con `{}`.
    mode : RuntimeMode
        Modo de ejecucion pedido.

    Returns
    -------
    int
        0 si la ejecucion fue exitosa, != 0 en caso de error (incl. event
        JSON inexistente o invalido).
    """
    event, error = _load_event(event_path)
    if error is not None:
        _err(error)
        return 1

    effective_mode = mode
    if effective_mode is RuntimeMode.RIE and not _docker_available():
        print(
            _c(
                YELLOW,
                '[WARN] Docker no esta disponible; '
                'run-local cae a modo directo.',
            ),
        )
        effective_mode = RuntimeMode.DIRECT

    if effective_mode is RuntimeMode.RIE:
        return _run_rie(resolved, event)
    return _run_direct(resolved, event)
