"""Controllers de la operation `register` del Lambda `auth`.

3 actions:
- `start` -> `start.py` + `Start`
- `verify-magic-link` -> `verify_magic_link.py` + `VerifyMagicLink`
- `verify-code` -> `verify_code.py` + `VerifyCode`

El import_controller del kit resuelve el modulo y la clase a partir
del nombre del action sent por el cliente (con guiones).
"""
