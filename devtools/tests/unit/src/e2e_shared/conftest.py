"""Conftest del paquete e2e_shared: resuelve `shared.config`, `shared.totp`,
etc. desde `tests/shared/`.

Estos tests importan el portador E2E (`tests/shared/`), que se expone como
el paquete top-level `shared`. Pero en el arbol de devtools ya existe OTRO
paquete top-level `shared` (`devtools/shared/`, con `commands`, `paths`,
...), que el conftest raiz de devtools pone en el `sys.path` y que los demas
tests importan. Cuando la suite completa corre (`pytest devtools/tests`),
`devtools/shared` queda bindeado en `sys.modules['shared']` ANTES de que se
colecte este paquete, asi que un simple `sys.path.insert` NO basta:
`import shared.config` busca `config` dentro de `devtools/shared` y no lo
encuentra.

Fix quirurgico y NO destructivo: los modulos del portador E2E
(`config`, `http`, `runner`, `reporter`, `totp`, ...) NO existen en
`devtools/shared` — los nombres no colisionan, solo el del paquete. Por eso
basta con AGREGAR `tests/shared/` al `__path__` del paquete `shared` (ya
sea el de devtools o el que se cree primero). Asi `shared.config` resuelve
desde `tests/shared/` y `shared.commands` sigue resolviendo desde
`devtools/shared/`, sin romper a los demas tests de devtools.
"""

from __future__ import annotations

import importlib
from pathlib import Path
import sys


# devtools/tests/unit/src/e2e_shared/conftest.py -> e2e_shared, src, unit,
# tests, devtools, ROOT  ==> parents[5] es la raiz del repo.
_TESTS_SHARED = Path(__file__).resolve().parents[5] / 'tests' / 'shared'


def _ensure_shared_path() -> None:
    """Asegura que `shared.__path__` incluya `tests/shared/`.

    Importa (o reutiliza) el paquete `shared` y extiende su `__path__` con
    el directorio del portador E2E si aun no esta. Idempotente.
    """
    shared = sys.modules.get('shared')
    if shared is None:
        # tests/ al frente para que, si `shared` aun no existe, el primer
        # import lo cree desde tests/shared (con su __init__.py propio).
        tests_dir = str(_TESTS_SHARED.parent)
        if tests_dir not in sys.path:
            sys.path.insert(0, tests_dir)
        shared = importlib.import_module('shared')
    search = str(_TESTS_SHARED)
    if search not in list(shared.__path__):
        shared.__path__.append(search)


_ensure_shared_path()
