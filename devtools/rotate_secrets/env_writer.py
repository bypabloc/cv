"""Helper: in-place updates to env files (KEY=value lines).

Sustituye lineas existentes con `KEY=...`. NO crea claves nuevas — si la key
no existe en el archivo, emite warning. Esto evita ensuciar el .env con keys
que el codigo no espera.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


def update_env_file(
    path: Path,
    updates: dict[str, str],
    *,
    dry_run: bool,
) -> list[str]:
    """Reemplaza lineas KEY=... en archivo .env. Retorna keys efectivamente
    cambiadas."""
    if not path.exists():
        sys.exit(f'ERROR: {path} no existe')

    original = path.read_text()
    new_text = original
    changed: list[str] = []

    for key, value in updates.items():
        pattern = re.compile(rf'^{re.escape(key)}=.*$', re.MULTILINE)
        if not pattern.search(new_text):
            print(f'  WARN: key {key} no existe en {path.name}, se omite')
            continue
        new_text = pattern.sub(f'{key}={value}', new_text)
        changed.append(key)

    if new_text == original:
        print(f'  {path.name}: sin cambios')
        return []

    if dry_run:
        print(f'  [dry-run] {path.name}: actualizaria {changed}')
        return changed

    path.write_text(new_text)
    print(f'  {path.name}: actualizado {changed}')
    return changed
