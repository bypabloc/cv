#!/usr/bin/env python3
"""Unified entry point for devtools scripts."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
from types import ModuleType

from utils.flags_to_dict import flags_to_dict


# Anadir el directorio raíz del proyecto al path para que los imports absolutos funcionen
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Anadir utils al path para usar flags_to_dict
utils_path = str(Path(__file__).parent / 'utils')
if utils_path not in sys.path:
    sys.path.append(utils_path)


# ---------------------------------------------------------------------------
# Auto-bootstrap: ensure devtools/.venv exists with deps from pyproject.toml
# Managed by `uv sync --project devtools` (Python 3.14, see devtools/pyproject.toml).
# ---------------------------------------------------------------------------

import os  # noqa: E402


_DEVTOOLS_DIR = Path(__file__).parent
_VENV_DIR = _DEVTOOLS_DIR / '.venv'
_PYPROJECT = _DEVTOOLS_DIR / 'pyproject.toml'
_LOCKFILE = _DEVTOOLS_DIR / 'uv.lock'

_UV_INSTALL_HINT = (
    'uv no esta instalado. Instalalo con:\n'
    '  curl -LsSf https://astral.sh/uv/install.sh | sh\n'
    'o ver https://docs.astral.sh/uv/getting-started/installation/'
)


def _ensure_uv_available() -> str:
    """Verify `uv` is on PATH; print install hint and exit if missing."""
    uv = shutil.which('uv')
    if uv is None:
        print(f'[devtools] {_UV_INSTALL_HINT}', file=sys.stderr)
        sys.exit(1)
    return uv


def _ensure_venv() -> None:
    """Create or sync devtools/.venv using `uv sync --project devtools`.

    Runs `uv sync` whenever:
      - devtools/.venv does not exist
      - the lockfile is newer than the venv (deps changed)

    `uv sync --frozen` ensures bit-perfect reproducibility against uv.lock.
    """
    if not _PYPROJECT.exists():
        return  # devtools not yet migrated; nothing to bootstrap

    uv = _ensure_uv_available()
    venv_python = _VENV_DIR / 'bin' / 'python'

    needs_sync = False
    if not venv_python.exists() or (
        _LOCKFILE.exists()
        and _LOCKFILE.stat().st_mtime > venv_python.stat().st_mtime
    ):
        needs_sync = True

    if not needs_sync:
        return

    # Bootstrap output va a stderr para no contaminar stdout — comandos
    # como --output=json o --generate-completion necesitan stdout limpio
    # para que el caller (jq, source, etc.) pueda parsear sin filtros.
    print(
        '[devtools] Sincronizando .venv (uv sync)...',
        file=sys.stderr,
        flush=True,
    )
    try:
        subprocess.run(  # noqa: S603
            [uv, 'sync', '--frozen', '--project', str(_DEVTOOLS_DIR)],
            check=True,
            timeout=180,
            stdout=sys.stderr,  # uv imprime 'Audited ...' a stdout por default
        )
    except subprocess.CalledProcessError as exc:
        print(f'[devtools] uv sync fallo: {exc}', file=sys.stderr)
        sys.exit(1)
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f'[devtools] uv sync timeout/error: {exc}', file=sys.stderr)
        sys.exit(1)


def _reexec_in_venv() -> None:
    """If we are not running inside devtools/.venv, re-exec with its python.

    Detection uses ``sys.prefix`` (not the executable path) because the venv
    in WSL2 may resolve all binaries through symlinks that point to system
    python; ``sys.prefix`` always reflects the active environment.
    """
    venv_python = _VENV_DIR / 'bin' / 'python'
    if not venv_python.exists():
        return  # Bootstrap already failed and exited; unreachable here.

    venv_prefix = str(_VENV_DIR.resolve())
    current_prefix = str(Path(sys.prefix).resolve())
    if current_prefix == venv_prefix:
        return  # Already inside the venv

    # Re-exec preserving original arguments
    os.execv(str(venv_python), [str(venv_python), *sys.argv])  # noqa: S606


_ensure_venv()
_reexec_in_venv()


def load_module_from_path(module_name: str, file_path: str) -> ModuleType:
    """Carga un módulo desde una ruta especifica."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        msg = f'No se pudo cargar el módulo desde {file_path}'
        raise ImportError(msg)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_valid_scripts() -> list[str]:
    """Descubre todos los scripts válidos en el directorio devtools/."""
    scripts_dir = Path(__file__).parent
    valid_scripts = []

    for item in scripts_dir.iterdir():
        if (
            item.is_dir()
            and item.name != 'utils'
            and not item.name.startswith('.')
        ):
            main_py = item / 'main.py'
            flags_py = item / 'flags.py'
            if main_py.exists() and flags_py.exists():
                valid_scripts.append(item.name)

    return sorted(valid_scripts)


def show_global_help() -> None:
    """Muestra la ayuda global con todos los scripts disponibles."""
    print('=== Devtools - Ayuda Global ===')
    print()
    print('Uso: python devtools/run.py <script> [flags...]')
    print()

    valid_scripts = discover_valid_scripts()

    if not valid_scripts:
        print('No se encontraron scripts válidos.')
        return

    print('Scripts disponibles:')
    print('-' * 40)

    for script_name in valid_scripts:
        print(f'\n  {script_name}')

    print('\n' + '=' * 50)
    print(
        'Para ayuda especifica de un script: python devtools/run.py <script> --help'
    )


def _show_script_help(script_dir: Path, script_folder: str) -> None:
    """Muestra ayuda especifica de un script."""
    print(f"=== Ayuda para '{script_folder}' ===")
    print()

    readme_path = script_dir / 'README.md'
    if readme_path.exists():
        content = readme_path.read_text(encoding='utf-8').strip()
        if content:
            print(content)
            return

    print(f'Sin documentación disponible para {script_folder}')


def _resolve_script_paths(script_folder: str) -> tuple[Path, Path, Path]:
    """Resolve and validate script directory and file paths."""
    scripts_dir = Path(__file__).parent
    script_dir = scripts_dir / script_folder
    main_py_path = script_dir / 'main.py'
    flags_py_path = script_dir / 'flags.py'

    if not script_dir.exists():
        valid_scripts = discover_valid_scripts()
        print(f"Error: La carpeta '{script_folder}' no existe en devtools/")
        if valid_scripts:
            print('Scripts disponibles:', ', '.join(valid_scripts))
        sys.exit(1)

    if not main_py_path.exists():
        print(f"Error: No se encontro 'main.py' en devtools/{script_folder}/")
        sys.exit(1)

    if not flags_py_path.exists():
        print(f"Error: No se encontro 'flags.py' en devtools/{script_folder}/")
        sys.exit(1)

    return script_dir, main_py_path, flags_py_path


def _run_script(
    script_folder: str,
    main_py_path: Path,
    flags_py_path: Path,
    flags_dict: dict,
) -> None:
    """Load and execute a script module."""
    flags_module = load_module_from_path(
        f'{script_folder}_flags', flags_py_path
    )

    if not hasattr(flags_module, 'flag'):
        print(f"Error: No se encontro la función 'flag' en {flags_py_path}")
        sys.exit(1)

    # Modo silent: cuando el caller pide --only-list o --output=json,
    # eliminamos los banners ('Procesando flags...', 'Ejecutando...') del
    # stdout para que el output sea pipe-friendly. El comando interno sigue
    # imprimiendo a stdout normal — solo los wrappers van a stderr.
    is_silent_mode = (
        flags_dict.get('only_list', False) or flags_dict.get('output') == 'json'
    )
    flags_dict['_invoked_from'] = 'cli'

    if not is_silent_mode:
        print(f'Procesando flags para {script_folder}...', file=sys.stderr)

    try:
        parsed_flags = flags_module.flag(flags_dict)
    except ValueError as e:
        print('\nError en la configuración:', file=sys.stderr)
        print(f'   {e!s}', file=sys.stderr)
        print('\nPara ver la ayuda completa, usa:', file=sys.stderr)
        print(
            f'   python devtools/run.py {script_folder} --help',
            file=sys.stderr,
        )
        sys.exit(1)

    main_module = load_module_from_path(f'{script_folder}_main', main_py_path)

    if not hasattr(main_module, 'main'):
        print(
            f"Error: No se encontro la función 'main' en {main_py_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not is_silent_mode:
        print(f'Ejecutando {script_folder}...', file=sys.stderr)
        print('-' * 50, file=sys.stderr)

    exit_code = main_module.main(parsed_flags)
    if isinstance(exit_code, int) and exit_code != 0:
        sys.exit(exit_code)


def _list_flags_for(script_folder: str) -> set[str]:
    """Return the set of flags that should be parsed as lists for a script.

    Reads ``describe()`` from the script's flags.py and picks any flag with
    ``type='list'``. This is the opt-in mechanism for the `|`-split behaviour
    in flags_to_dict (see Fase 6 of the CLI refactor).
    """
    described = _load_describe(script_folder)
    if not described:
        return set()
    return {
        name
        for name, spec in described.get('flags', {}).items()
        if spec.get('type') == 'list'
    }


def _load_describe(script_folder: str) -> dict | None:
    """Load ``describe()`` from a script's flags.py if present."""
    scripts_dir = Path(__file__).parent
    flags_py = scripts_dir / script_folder / 'flags.py'
    if not flags_py.exists():
        return None
    try:
        flags_module = load_module_from_path(
            f'{script_folder}_flags_describe',
            str(flags_py),
        )
    except (ImportError, OSError):
        return None
    describe_fn = getattr(flags_module, 'describe', None)
    if describe_fn is None:
        return None
    try:
        return describe_fn()
    except (ValueError, TypeError, AttributeError):
        return None


def _list_scripts_payload() -> list[dict]:
    """Inventory of every devtools script (uses describe() when available)."""
    inventory: list[dict] = []
    for script_name in discover_valid_scripts():
        described = _load_describe(script_name)
        if described:
            inventory.append(
                {
                    'name': described.get('name', script_name),
                    'kind': described.get('kind', 'monocommand'),
                    'summary': described.get('summary', ''),
                    'has_describe': True,
                }
            )
        else:
            inventory.append(
                {
                    'name': script_name,
                    'kind': 'unknown',
                    'summary': '',
                    'has_describe': False,
                }
            )
    return inventory


def _emit_introspection(payload: object, *, output: str) -> None:
    """Emit introspection data as JSON (used for both --output=json and text)."""
    import json

    del output  # both modes emit JSON for now; reserved for future plain-text
    print(json.dumps(payload, indent=2, default=str, ensure_ascii=False))


def _generate_zsh_completion() -> str:
    """Generate a zsh completion script using describe() metadata.

    The script is regenerable on demand: run again whenever you add a new
    command and source the output. No manual edits needed.
    """
    scripts = []
    for script_name in discover_valid_scripts():
        described = _load_describe(script_name)
        if not described:
            scripts.append({'name': script_name, 'kind': 'unknown'})
            continue
        scripts.append(described)

    lines = [
        '#compdef devtools',
        '# zsh completion for `python devtools/run.py`. Source this file from',
        '# your zshrc.d/ to enable tab-complete on scripts and subcommands.',
        '',
        '_devtools() {',
        '  local context state line',
        '  typeset -A opt_args',
        '  _arguments -C \\',
        "    '1: :_devtools_scripts' \\",
        "    '*::arg:->args'",
        '  case $state in',
        '    args)',
        '      case $line[1] in',
    ]

    for s in scripts:
        name = s['name']
        if s.get('kind') == 'subcommand':
            cmds_alts = ' '.join(
                f"'{c['name']}:{c.get('summary', '')}'"
                for c in s.get('commands', [])
            )
            lines.extend(
                [
                    f'        {name})',
                    f'          _values "{name} command" {cmds_alts}',
                    '          ;;',
                ]
            )
        else:
            flag_alts = []
            for fname, fspec in s.get('flags', {}).items():
                flag_alts.append(
                    f"'--{fname.replace('_', '-')}[{fspec.get('summary', '')}]'"
                )
            joined = ' '.join(flag_alts)
            lines.extend(
                [
                    f'        {name})',
                    f'          _arguments {joined}',
                    '          ;;',
                ]
            )

    lines.extend(
        [
            '      esac',
            '      ;;',
            '  esac',
            '}',
            '',
            '_devtools_scripts() {',
            '  local -a scripts',
            '  scripts=(',
        ]
    )
    lines.extend(f'    "{s["name"]}:{s.get("summary", "")}"' for s in scripts)
    lines.extend(
        [
            '  )',
            '  _describe "script" scripts',
            '}',
            '',
            'compdef _devtools devtools',
        ]
    )
    return '\n'.join(lines) + '\n'


def _generate_bash_completion() -> str:
    """Generate a bash completion script using describe() metadata."""
    scripts = []
    for script_name in discover_valid_scripts():
        described = _load_describe(script_name)
        scripts.append((script_name, described))

    script_names = ' '.join(name for name, _ in scripts)

    lines = [
        '# bash completion for `python devtools/run.py`. Source from your',
        '# bashrc to enable tab-complete on scripts and subcommands.',
        '_devtools_complete() {',
        '  local cur prev words cword',
        '  COMPREPLY=()',
        '  cur="${COMP_WORDS[COMP_CWORD]}"',
        '  prev="${COMP_WORDS[COMP_CWORD-1]}"',
        '',
        '  # First arg: the script name',
        '  if [[ $COMP_CWORD -eq 2 ]]; then',
        f'    COMPREPLY=( $(compgen -W "{script_names}" -- "$cur") )',
        '    return 0',
        '  fi',
        '',
        '  # Second arg: subcommand or flag depending on script kind',
        '  case "${COMP_WORDS[2]}" in',
    ]
    for name, described in scripts:
        if not described:
            continue
        if described.get('kind') == 'subcommand':
            cmd_names = ' '.join(
                c['name'] for c in described.get('commands', [])
            )
            lines.extend(
                [
                    f'    {name})',
                    f'      COMPREPLY=( $(compgen -W "{cmd_names}" -- "$cur") )',
                    '      ;;',
                ]
            )
        else:
            flag_names = ' '.join(
                f'--{f.replace("_", "-")}' for f in described.get('flags', {})
            )
            lines.extend(
                [
                    f'    {name})',
                    f'      COMPREPLY=( $(compgen -W "{flag_names}" -- "$cur") )',
                    '      ;;',
                ]
            )
    lines.extend(
        [
            '  esac',
            '}',
            '',
            'complete -F _devtools_complete devtools',
        ]
    )
    return '\n'.join(lines) + '\n'


def _handle_introspection(flags_dict: dict, script_folder: str | None) -> bool:
    """Dispatch the introspection flags. Returns True if handled."""
    output = flags_dict.get('output', 'text')
    if output not in ('text', 'json'):
        print(f"Output inválido: '{output}'. Válidos: text, json")
        sys.exit(1)

    if flags_dict.get('list_scripts'):
        _emit_introspection(_list_scripts_payload(), output=output)
        return True

    if script_folder is None:
        return False

    if (
        flags_dict.get('list_commands')
        or flags_dict.get('list_flags')
        or flags_dict.get('describe')
    ):
        described = _load_describe(script_folder)
        if described is None:
            print(
                f"Script '{script_folder}' no expone describe(). "
                'Aniade `def describe() -> ScriptDescribe` en flags.py.'
            )
            sys.exit(1)
        if flags_dict.get('describe'):
            # --describe emite el describe() completo (name + kind + summary
            # + commands + flags). Es la union de --list-commands + --list-flags.
            _emit_introspection(described, output=output)
        elif flags_dict.get('list_flags'):
            _emit_introspection(described.get('flags', {}), output=output)
        else:
            payload = {k: v for k, v in described.items() if k != 'flags'}
            _emit_introspection(payload, output=output)
        return True

    return False


def _emit_completion(argv: list[str]) -> None:
    """Print the requested shell completion script and exit cleanly."""
    flags_dict = flags_to_dict(argv)
    shell = flags_dict.get('generate_completion', 'zsh')
    if shell == 'zsh':
        print(_generate_zsh_completion(), end='')
    elif shell == 'bash':
        print(_generate_bash_completion(), end='')
    else:
        print(
            f"Shell inválido: '{shell}'. Válidos: zsh, bash",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    """Ejecutor principal del sistema de devtools."""
    if len(sys.argv) == 2 and sys.argv[1] == '--help':
        show_global_help()
        sys.exit(0)

    if len(sys.argv) < 2:
        print('Uso: python devtools/run.py <script> [flags...]')
        print(
            '      python devtools/run.py --help  (para ver todos los scripts)'
        )
        print('      python devtools/run.py --list-scripts --output=json')
        sys.exit(1)

    # Top-level introspection: --list-scripts antes que cualquier script.
    if sys.argv[1] == '--list-scripts':
        flags_dict = flags_to_dict(sys.argv[1:])
        if _handle_introspection(flags_dict, None):
            sys.exit(0)
        sys.exit(1)

    # Top-level: --generate-completion=zsh|bash
    if sys.argv[1].startswith('--generate-completion'):
        _emit_completion(sys.argv[1:])
        sys.exit(0)

    script_folder = sys.argv[1]
    flags_dict = flags_to_dict(
        sys.argv[2:],
        list_flags=_list_flags_for(script_folder),
    )

    # Per-script introspection (--list-commands / --list-flags / --describe)
    # corre antes de la validación del script para que funcione incluso con
    # scripts que no han migrado todas sus flags.
    introspection_requested = (
        flags_dict.get('list_commands')
        or flags_dict.get('list_flags')
        or flags_dict.get('describe')
    )
    if introspection_requested and _handle_introspection(
        flags_dict, script_folder
    ):
        sys.exit(0)

    script_dir, main_py_path, flags_py_path = _resolve_script_paths(
        script_folder,
    )

    if flags_dict.get('help', False):
        _show_script_help(script_dir, script_folder)
        sys.exit(0)

    try:
        _run_script(script_folder, main_py_path, flags_py_path, flags_dict)
    except (ImportError, AttributeError, ValueError, TypeError, OSError) as e:
        print(f'Error ejecutando el script: {e}')
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
