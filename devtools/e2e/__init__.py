"""Comando `e2e`: orquestador unificado de los E2E del portfolio.

Monocommand Python 3.14 que corre los tests E2E (modulos `api`, `admin`,
`app`) contra el entorno DESPLEGADO (dev, NUNCA prod). Reemplaza al
viejo `api_e2e` + el modulo `feature` de `test_runner`. Detalle de la
arquitectura en `devtools/e2e/README.md`.
"""
