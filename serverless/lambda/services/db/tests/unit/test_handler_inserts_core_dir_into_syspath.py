"""Handler — bootstrap del sys.path.

Given un sys.path que NO contiene el directorio core/ del Lambda,
When el modulo handler se ejecuta como modulo fresco,
Then inserta core/ al frente de sys.path para que los imports absolutos
     del Lambda resuelvan.
"""

import importlib.util
import os
import sys

import pytest

pytestmark = pytest.mark.unit


def test_handler_inserts_core_dir_into_syspath():
    import handler as loaded_handler

    # Arrange: core/ es el directorio donde vive handler.py.
    handler_path = os.path.abspath(loaded_handler.__file__)
    core_dir = os.path.dirname(handler_path)
    original = list(sys.path)
    while core_dir in sys.path:
        sys.path.remove(core_dir)

    # Act: ejecutar handler.py como modulo fresco con core_dir fuera del
    # path -> la rama `if _CORE_DIR not in sys.path` corre el insert.
    try:
        spec = importlib.util.spec_from_file_location(
            'handler_bootstrap_probe', handler_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        present_after_exec = core_dir in sys.path
    finally:
        sys.path[:] = original
        if core_dir not in sys.path:
            sys.path.insert(0, core_dir)
        sys.modules.pop('handler_bootstrap_probe', None)

    # Assert
    assert present_after_exec is True
