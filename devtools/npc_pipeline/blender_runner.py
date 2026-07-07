"""Build and run headless Blender invocations for the NPC pipeline.

Blender is a system binary the developer installs locally (not a
monorepo/devtools dependency) — see
.claude/docs/journey-npc-realism/01-pipeline-blender-headless.md. This
module never assumes it is installed: every entry point degrades to a
clear, actionable ``NpcPipelineError`` instead of a bare traceback.
"""

from pathlib import Path
import re
import subprocess


MIN_BLENDER_VERSION = (4, 2)
_SCRIPTS_DIR = Path(__file__).resolve().parent / 'scripts'
_DOCS_HINT = '.claude/docs/journey-npc-realism/01-pipeline-blender-headless.md'


class NpcPipelineError(Exception):
    """User-facing error for the npc_pipeline devtools script."""


def find_blender_version(
    *,
    blender_bin: str = 'blender',
) -> tuple[int, int, int] | None:
    """Return the installed Blender version, or ``None`` if not found."""
    try:
        # S603/S607: binario resuelto via PATH (o --blender-bin explicito
        # del dev), args fijos — igual patron que serverless/*.py.
        result = subprocess.run(  # noqa: S603
            [blender_bin, '--version'],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError:
        return None

    if result.returncode != 0:
        return None

    match = re.search(r'Blender (\d+)\.(\d+)\.(\d+)', result.stdout)
    if not match:
        return None

    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def check_blender_available(
    *,
    blender_bin: str = 'blender',
) -> tuple[bool, str]:
    """Check Blender is installed and meets ``MIN_BLENDER_VERSION``.

    Returns ``(ok, message)``: ``message`` is always human-readable so
    ``npc_pipeline status`` (and every other subcommand, on failure) can
    print it directly instead of a stack trace.
    """
    version = find_blender_version(blender_bin=blender_bin)
    required = '.'.join(str(p) for p in MIN_BLENDER_VERSION)

    if version is None:
        return False, (
            f"Blender no encontrado en PATH (binario: '{blender_bin}'). "
            'Es un requisito manual del desarrollador (instalar desde '
            'blender.org, sin cuenta) — NO es una dependencia del '
            f'monorepo. Ver {_DOCS_HINT}.'
        )

    if version[:2] < MIN_BLENDER_VERSION:
        found = '.'.join(str(p) for p in version)
        return False, (
            f'Blender {found} encontrado, pero MPFB2 requiere >= {required}.'
            ' Actualizalo desde blender.org.'
        )

    found = '.'.join(str(p) for p in version)
    return True, f'Blender {found} OK (>= {required} requerido por MPFB2).'


def script_path(name: str) -> Path:
    """Resolve a bpy script path within ``npc_pipeline/scripts/``."""
    path = _SCRIPTS_DIR / name
    if not path.exists():
        msg = f'Script bpy no encontrado: {path}'
        raise NpcPipelineError(msg)
    return path


def build_blender_command(
    *,
    script_name: str,
    script_args: list[str],
    blender_bin: str = 'blender',
) -> list[str]:
    """Build the ``blender --background --python ... -- ...`` argv list.

    ``--python-exit-code 1`` es OBLIGATORIO: sin el, Blender exit-ea 0
    aunque el script Python lance una excepcion sin capturar (solo
    imprime el traceback y sigue) — descubierto corriendo el pipeline
    real, no era evidente por la documentacion.
    """
    return [
        blender_bin,
        '--background',
        '--python-exit-code',
        '1',
        '--python',
        str(script_path(script_name)),
        '--',
        *script_args,
    ]


def run_blender_script(
    *,
    script_name: str,
    script_args: list[str],
    blender_bin: str = 'blender',
    timeout: int = 600,
) -> subprocess.CompletedProcess:
    """Run a bpy script headless; raise ``NpcPipelineError`` on any failure.

    Callers get stdout/stderr embedded in the exception message for
    diagnosis — never a bare non-zero exit with no context.
    """
    ok, message = check_blender_available(blender_bin=blender_bin)
    if not ok:
        raise NpcPipelineError(message)

    command = build_blender_command(
        script_name=script_name,
        script_args=script_args,
        blender_bin=blender_bin,
    )
    # S603: comando armado por devtools (binario fijo + script/args propios).
    result = subprocess.run(  # noqa: S603
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        msg = (
            f'Blender script {script_name!r} fallo '
            f'(exit {result.returncode}).\n'
            f'stdout:\n{result.stdout}\nstderr:\n{result.stderr}'
        )
        raise NpcPipelineError(msg)

    return result
