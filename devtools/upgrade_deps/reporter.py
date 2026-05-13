"""Reporte tabular de resultados del upgrade."""

# Colores ANSI minimos (mismos codes que .git-hooks/_common.py)
_GREEN = '\033[0;32m'
_YELLOW = '\033[1;33m'
_CYAN = '\033[0;36m'
_RED = '\033[0;31m'
_NC = '\033[0m'

ACTION_UP = 'upgrade'
ACTION_OK = 'ok'
ACTION_SKIP = 'skip'
ACTION_ERROR = 'error'


def format_action(action: str) -> str:
    """Color-code la accion para legibilidad en terminal."""
    if action == ACTION_UP:
        return f'{_YELLOW}{action:>8}{_NC}'
    if action == ACTION_OK:
        return f'{_GREEN}{action:>8}{_NC}'
    if action == ACTION_ERROR:
        return f'{_RED}{action:>8}{_NC}'
    return f'{_CYAN}{action:>8}{_NC}'


def print_table(rows: list[dict], *, manifest: str) -> None:
    """Imprime una tabla con: package | actual | latest | accion."""
    print()
    print(f'{_CYAN}=== {manifest} ==={_NC}')

    if not rows:
        print('  (sin paquetes)')
        return

    # Anchos fijos para alineacion legible
    name_w = max(len(r['name']) for r in rows)
    cur_w = max(len(r['current']) for r in rows)
    lat_w = max(len(r['latest'] or '-') for r in rows)
    name_w = max(name_w, 30)
    cur_w = max(cur_w, 10)
    lat_w = max(lat_w, 10)

    header = (
        f'  {"package":<{name_w}}  '
        f'{"current":<{cur_w}}  {"latest":<{lat_w}}  action'
    )
    print(header)
    print('  ' + '-' * (len(header) - 2))

    for row in rows:
        name = row['name']
        current = row['current']
        latest = row['latest'] or '-'
        action = format_action(row['action'])
        print(
            f'  {name:<{name_w}}  {current:<{cur_w}}  {latest:<{lat_w}}  {action}'
        )


def print_summary(stats: dict) -> None:
    """Imprime resumen agregado al final."""
    print()
    print(f'{_CYAN}{"=" * 60}{_NC}')
    print(
        f'  Resumen: {stats["upgraded"]} upgrades | '
        f'{stats["ok"]} ya en latest | '
        f'{stats["skip"]} omitidos | '
        f'{stats["error"]} errores'
    )
    print(f'{_CYAN}{"=" * 60}{_NC}')
