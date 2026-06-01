"""api_e2e — tests E2E reales contra el backend serverless desplegado.

Corre los flujos completos (exito + errores) de cada Lambda HTTP del
portfolio (cv, contact_form, tracking_pixel, auth, users) contra un
entorno de DEPLOY real (dev | stage, NUNCA prod) via HTTP (httpx),
midiendo el tiempo de respuesta de cada endpoint.

NO es parte de `test_runner` (cuyo `--type=all` corre en CI/pre-push y
cuyos `--env` son entornos Docker local/dev/test): estos tests MUTAN el
entorno desplegado, leen secretos de SSM y siembran hashes en Neon, asi
que son un comando devtools dedicado, opt-in, fuera de la bateria de CI.
"""
