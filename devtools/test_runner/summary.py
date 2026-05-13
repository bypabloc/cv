"""Summary printing and final exit-code evaluation for the test_runner."""

from __future__ import annotations

from shared.console import CYAN
from shared.console import GREEN
from shared.console import NC
from shared.console import RED
from shared.console import YELLOW
from shared.console import _err
from shared.console import _ok
from shared.console import _warn


def _build_replay_cmd(key: str) -> str:
    """Build a CLI command to replay a specific failed test ('module:type')."""
    parts = key.split(':', 1)
    module = parts[0]
    test_type = parts[1] if len(parts) > 1 else 'all'
    return f'python devtools/run.py test_runner --module={module} --type={test_type}'


def print_summary(results: dict[str, int]) -> None:
    """Print a summary table with replay commands for any failures."""
    print()
    print(f'{CYAN}{"=" * 60}{NC}')
    print(f'{CYAN} Resumen{NC}')
    print(f'{CYAN}{"=" * 60}{NC}')
    print(f'  {"Módulo":<30} {"Estado":>10}')
    print(f'  {"-" * 30} {"-" * 10}')

    for module, exit_code in results.items():
        if exit_code == 0:
            status = f'{GREEN}OK{NC}'
        elif exit_code == -1:
            status = f'{YELLOW}SKIP{NC}'
        else:
            status = f'{RED}FAIL{NC}'
        print(f'  {module:<30} {status:>20}')

    failures = [key for key, code in results.items() if code > 0]
    if failures:
        print()
        print(f'{YELLOW}Replicar fallos:{NC}')
        for key in failures:
            print(f'  {_build_replay_cmd(key)}')

    print()


def evaluate_results(
    results: dict[str, int],
    *,
    skip_empty: bool,
) -> int:
    """Reduce per-result codes to a single exit code for the runner."""
    failures = [key for key, code in results.items() if code > 0]
    if failures:
        _err(f'Tests fallaron en: {", ".join(failures)}')
        return 1

    all_skipped = all(code == -1 for code in results.values())
    if all_skipped:
        if skip_empty:
            _warn('Todos los módulos saltados (sin archivos cambiados)')
            return 0
        _err('No se ejecutaron tests (sin archivos cambiados)')
        return 1

    _ok('Todos los tests pasaron')
    return 0
