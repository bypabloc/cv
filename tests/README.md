# Tests E2E del portfolio (Python 3.14)

> Suite E2E unificada contra el entorno DESPLEGADO (dev), en Python
> 3.14 (`devtools/.venv`). UN comando, tres modulos: `api` (Lambdas HTTP),
> `admin` (panel Next.js, browser) y `app` (las 6 apps Astro, browser).

## Como correr

El orquestador es el comando `e2e` de devtools (se implementa en una fase
posterior del plan). Forma canonica:

```bash
python devtools/run.py e2e --module=<api|admin|app> --env=dev
```

Mientras tanto, los modulos se pueden invocar directo con pytest bajo el
interprete correcto (NUNCA el `python3` del shell, que es 3.12):

```bash
# desde la raiz del repo
devtools/.venv/bin/python -m pytest tests/api  --env=dev
devtools/.venv/bin/python -m pytest tests/app  --env=dev
devtools/.venv/bin/python -m pytest tests/admin --env=dev
```

Opciones (en `tests/conftest.py`): `--env` (dev, default dev),
`--aws-profile`, `--samples` (modulo api), `--keep-data`, `--lambda`.

## Estructura

```text
tests/
├── conftest.py     # opciones CLI + fixtures de sesion (env, aws_profile, ...)
├── pyproject.toml  # config pytest (testpaths, markers, pythonpath)
├── shared/         # PORTADOR de herramientas E2E (config, http, runner,
│                   #   reporter, totp, auth_support, environment, browser)
├── api/            # modulo api — Lambdas HTTP (httpx puro)
├── admin/          # modulo admin — flujos del panel admin (browser)
├── app/            # modulo app — las 6 apps Astro (browser)
└── results/        # output (PNG, json) — GITIGNORED
```

`shared/` se importa como paquete top-level `shared.*` (con `tests/` en el
`sys.path`). NO confundir con `devtools/shared/`: son dos paquetes `shared`
distintos que nunca conviven en el mismo `sys.path`.

## Reglas

- SIEMPRE Python 3.14 (`devtools/.venv`), NUNCA TypeScript en E2E.
- SIEMPRE contra dev desplegado, NUNCA prod, NUNCA stack Docker local.
- SIEMPRE hermetico: ningun valor de secreto (bypass, Neon URL) a stdout.
- Los modulos `api`/`admin` exigen credenciales (SSO + clave privada Ed25519
  local); sin ellas fallan duro. El modulo `app` (no-auth) puede correr sin.

Reglas completas: `.claude/rules/e2e-testing.md` (se crea en una fase
posterior del plan).
