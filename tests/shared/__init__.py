"""Portador unico de herramientas E2E (Python 3.14) para el arbol tests/.

Reune la maquinaria compartida por los modulos `api`, `admin` y `app`:
config (URLs por env, IpRotator, emails sinteticos), cliente HTTP con
timing, runner + reporter de tiempos, TOTP, helpers de auth, el harness
de browser (playwright-python) y el acceso al entorno desplegado (bypass
firmado + Neon seed/cleanup).

Se importa como paquete top-level `shared.*` cuando `tests/` esta en el
`sys.path` (lo configura `tests/conftest.py` + `tests/pyproject.toml`
`pythonpath = ['.']`). NO confundir con `devtools/shared/` (otro paquete
top-level `shared` del CLI): los dos NUNCA conviven en el mismo
`sys.path`; cada arbol los resuelve por separado.
"""
