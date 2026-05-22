"""Wrapper unico sobre el AWS CLI.

Antes de la migracion sin SAM, cada modulo del backend serverless armaba
su propio `_aws()` (`infra_deploy.py`, `lambda_controller.py`). Este
modulo centraliza la invocacion de `aws ...`: inyecta `--profile` y
`--region`, parsea JSON, normaliza errores y expone un helper de
idempotencia (`aws_resource_exists`).

Toda llamada AWS del backend debe pasar por aqui — NUNCA un
`subprocess.run(['aws', ...])` disperso.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from typing import Any


# Region por defecto del backend del portfolio.
DEFAULT_REGION = 'us-east-1'


class AwsError(RuntimeError):
    """Fallo de un comando aws CLI.

    Attributes
    ----------
    returncode : int
        Exit code del proceso `aws`.
    stderr : str
        Salida de error del comando.
    args_used : list[str]
        Argumentos AWS que se ejecutaron (sin el binario `aws`).
    """

    def __init__(
        self,
        message: str,
        *,
        returncode: int,
        stderr: str,
        args_used: list[str],
    ) -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr
        self.args_used = args_used


@dataclass(frozen=True)
class AwsResult:
    """Resultado de una invocacion del AWS CLI.

    Attributes
    ----------
    returncode : int
        Exit code del proceso.
    stdout : str
        Salida estandar (sin recortar).
    stderr : str
        Salida de error.
    json : Any
        stdout parseado como JSON, o None si `parse_json` era False o el
        stdout estaba vacio.
    """

    returncode: int
    stdout: str
    stderr: str
    json: Any = None

    @property
    def ok(self) -> bool:
        """True si el comando termino con exit code 0."""
        return self.returncode == 0


def aws(
    args: list[str],
    *,
    profile: str | None = None,
    region: str = DEFAULT_REGION,
    parse_json: bool = False,
    check: bool = True,
) -> AwsResult:
    """Ejecuta `aws <args>` y devuelve un `AwsResult`.

    Parameters
    ----------
    args : list[str]
        Argumentos del comando AWS (sin el binario `aws`). Ej:
        `['dynamodb', 'describe-table', '--table-name', 'x']`.
    profile : str | None
        Si no es None, inyecta `--profile <profile>`.
    region : str
        Region AWS; siempre se inyecta `--region <region>`.
    parse_json : bool
        Si True, parsea stdout como JSON y lo deja en `AwsResult.json`.
    check : bool
        Si True y el comando falla (returncode != 0), lanza `AwsError`.

    Returns
    -------
    AwsResult
        Resultado de la invocacion.

    Raises
    ------
    AwsError
        Si `check=True` y el comando termino con returncode != 0.
    """
    cmd = ['aws', *args, '--region', region]
    if profile:
        cmd += ['--profile', profile]


    # derivados de config del repo, sin input de usuario no confiable.
    completed = subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    if check and completed.returncode != 0:
        raise AwsError(
            f'Comando aws fallo (exit {completed.returncode}): '
            f'{" ".join(args)}',
            returncode=completed.returncode,
            stderr=completed.stderr.strip(),
            args_used=args,
        )

    parsed: Any = None
    if parse_json and completed.stdout.strip():
        try:
            parsed = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise AwsError(
                f'La salida de aws no es JSON valido: {" ".join(args)}',
                returncode=completed.returncode,
                stderr=str(exc),
                args_used=args,
            ) from exc

    return AwsResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        json=parsed,
    )


def aws_resource_exists(
    service: str,
    describe_args: list[str],
    *,
    profile: str | None = None,
    region: str = DEFAULT_REGION,
) -> bool:
    """True si un `aws <service> <describe_args>` retorna exit code 0.

    Sirve para idempotencia: antes de crear un recurso, se consulta si ya
    existe con su comando `describe-*` / `get-*`. Cualquier returncode
    distinto de 0 (recurso ausente, error de permisos, etc.) se trata
    como "no existe" desde el punto de vista del llamador, que decidira
    si crearlo.

    Parameters
    ----------
    service : str
        Servicio AWS (ej. `dynamodb`, `lambda`, `iam`).
    describe_args : list[str]
        Resto del comando describe/get (sin `aws` ni el servicio).
    profile : str | None
        Perfil AWS opcional.
    region : str
        Region AWS.

    Returns
    -------
    bool
        True si el comando termino con exit code 0.
    """
    result = aws(
        [service, *describe_args],
        profile=profile,
        region=region,
        check=False,
    )
    return result.ok
