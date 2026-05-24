"""Wrapper de `gh` para gestionar GitHub Environment Variables.

Hermetico: el valor NUNCA aparece en stdout ni en mensajes de error.
"""

import hashlib
import subprocess


class GhClientError(RuntimeError):
    """Error invocando gh. NO contiene el valor del secreto."""


def check_auth() -> None:
    """Falla con GhClientError si gh no esta autenticado."""
    result = subprocess.run(
        ['gh', 'auth', 'status'],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GhClientError(
            'GitHub CLI no autenticado. Ejecuta: gh auth login',
        )


def ensure_environment(env: str) -> None:
    """Crea el GH Environment si no existe (idempotente).

    Usa la REST API: PUT /repos/{owner}/{repo}/environments/{env}.
    Si ya existe, devuelve 200; si no, lo crea con 201.
    """
    repo = _current_repo()
    result = subprocess.run(  # noqa: S603
        [
            'gh',
            'api',
            '-X',
            'PUT',
            f'repos/{repo}/environments/{env}',
            '--silent',
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GhClientError(
            f'No pude crear/asegurar el GH Environment "{env}": '
            f'{result.stderr.strip()}',
        )


def get_variable(env: str, name: str) -> str | None:
    """Devuelve el valor actual de una GH Environment Variable o None.

    NO imprime el valor — solo lo retorna para que el caller calcule
    su hash y lo descarte de inmediato.
    """
    repo = _current_repo()
    result = subprocess.run(  # noqa: S603
        [
            'gh',
            'api',
            f'repos/{repo}/environments/{env}/variables/{name}',
            '-q',
            '.value',
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        # 404 -> no existe. Cualquier otro error -> propagar.
        stderr = result.stderr.lower()
        if 'http 404' in stderr or 'not found' in stderr:
            return None
        raise GhClientError(
            f'gh api fallo leyendo variable {name} de env {env}: '
            f'{result.stderr.strip()}',
        )
    return result.stdout.rstrip('\n')


def set_variable(env: str, name: str, value: str) -> None:
    """Crea o actualiza una GH Environment Variable.

    `gh` infiere el repo del cwd (git remote). El valor se pasa por --body;
    es publico (PUBLIC_*) por contrato, no aparece en stdout del CLI.
    """
    # NOTA: `gh variable set` con --body SI envia el valor en argv (visible
    # en ps aux corriendose). Como las keys de este script son PUBLIC_* por
    # contrato (no secrets), es aceptable. Si en el futuro se quiere
    # sincronizar Secrets, usar --body-file con tempfile 0600.
    result = subprocess.run(  # noqa: S603
        [
            'gh',
            'variable',
            'set',
            name,
            '--env',
            env,
            '--body',
            value,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        # NO incluir el valor en el error
        raise GhClientError(
            f'gh variable set fallo para {name} en env {env}: '
            f'{result.stderr.strip()}',
        )


def hash_value(value: str) -> str:
    """SHA256 truncado a 8 chars para comparar sin imprimir el valor."""
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:8]


def _current_repo() -> str:
    """Devuelve "owner/repo" del git remote actual via gh."""
    result = subprocess.run(
        [
            'gh',
            'repo',
            'view',
            '--json',
            'nameWithOwner',
            '-q',
            '.nameWithOwner',
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GhClientError(
            'No pude resolver el repo actual. ¿Estas en un git repo con remote GitHub?',
        )
    return result.stdout.strip()
