"""Unit tests del portador E2E (`tests/shared/`).

Espejo bajo devtools/tests/ de los modulos puros de `tests/shared/` (config,
reporter, runner, totp): los que NO requieren red ni AWS. El `conftest.py`
de este paquete agrega la carpeta `tests/` del repo al `sys.path` para que
`import shared.X` resuelva a `tests/shared/`, NO a `devtools/shared/`.
"""
