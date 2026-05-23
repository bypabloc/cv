# Fase 4 — Modo `--stage=local` (sin SSM, env vars directas)

> Define cómo el Lambda corre en local sin tocar AWS, leyendo las env vars
> directo del `docker/env/server/.local`. Garantiza el modo offline-dev.

## Modos de ejecución del Lambda

| Stage | Fuente de los secretos | Cómo el código del Lambda los lee |
|-------|------------------------|-----------------------------------|
| `local` (RIE o direct) | `docker/env/server/.local` inyectado como env del proceso | `os.environ[target_env_var_local]` (ver abajo) |
| `dev`/`stage`/`prod` | SSM Parameter Store | `ssm:GetParameter(os.environ[target_env_var])` |

## Decisión: dos nombres de env var, uno por modo

Cada `SecretSpec` declara `target_env_var` (el nombre del path SSM en el
Lambda). En modo cloud, el código lee:

```python
path = os.environ['SSM_NEON_URL_PATH']
db_url = ssm.get_parameter(Name=path, WithDecryption=True)['Parameter']['Value']
```

En modo local, queremos que el código lea el VALOR directo (sin SSM).
Opciones:

### Opción A: dos env vars, decisión en el código del Lambda *(recomendada)*

`target_env_var` (ej. `SSM_NEON_URL_PATH`) sigue siendo el path SSM.
En modo local, devtools inyecta TAMBIÉN el `source_env_var` (ej. `DB_URL`)
con el valor directo. El código del Lambda hace:

```python
def get_neon_url() -> str:
    """Resuelve DB_URL: en cloud via SSM, en local via env directa."""
    direct = os.environ.get('DB_URL')
    if direct:
        return direct  # local mode
    path = os.environ['SSM_NEON_URL_PATH']
    return _ssm_get(path)
```

Ventajas:
- Cero cambios en el código que ya lee SSM en cloud.
- Una sola línea de "trampa" en el helper de cada secreto.
- El catálogo NO necesita un campo nuevo: `source_env_var` ya es el
  nombre canónico de la env var local.

### Opción B: el código lee siempre `target_env_var`, devtools setea el path SSM en cloud y el VALOR en local

Más limpio para el código (siempre lee `target_env_var`), pero confunde
el sentido del nombre (`SSM_NEON_URL_PATH` con un valor no-path en local
es engañoso).

→ **Elegimos opción A**.

## Inyección de env vars en modo local

`serverless run --stage=local --lambda=contact_form --event=events/X.json`
o `serverless deploy --stage=local` (deploy local solo prepara el runtime):

```python
def _build_local_env(
    lambda_root: Path,
    env_file: Path,
    catalog: Catalog,
) -> dict[str, str]:
    """Construye el dict de env vars para el Lambda local.

    Incluye:
      - LOG_LEVEL, CORS_ALLOWED_ORIGINS, AWS_SES_REGION, etc. del
        manifest.yaml `env.{default,local}`.
      - Para cada SecretSpec con stage=local enabled (TODOS si tiene la
        keyword 'local' permitida — actualmente lo bloqueamos): inyectar
        `source_env_var=<valor del .env>`.

    NO inyecta SSM_<X>_PATH (no hay SSM en local). El codigo del Lambda
    decide via opcion A: si source_env_var presente => modo local.
    """
    env_values = _load_env_file_securely(env_file)
    runtime_env: dict[str, str] = {}

    # 1) env del manifest.yaml
    manifest = _read_manifest(lambda_root / 'manifest.yaml')
    runtime_env.update(manifest.get('env', {}).get('default', {}))
    runtime_env.update(manifest.get('env', {}).get('local', {}))

    # 2) inyectar source_env_var de cada secreto USADO por el lambda
    used_secrets = manifest.get('uses', {}).get('secrets', [])
    for short_name in used_secrets:
        spec = catalog.get(short_name)
        if spec.source_env_var not in env_values:
            if spec.required:
                raise SecretsSyncError(
                    f'.local sin {spec.source_env_var} (requerido por '
                    f'lambda {manifest["name"]}, secreto {short_name})',
                )
            continue  # opcional, skip
        runtime_env[spec.source_env_var] = env_values[spec.source_env_var]

    return runtime_env
```

## Cambio en el código del Lambda (uso del catálogo)

Cada Lambda que hoy lee SSM directo recibe un pequeño helper. Ubicación
sugerida: `serverless/lambda/shared/aws/ssm/__init__.py`:

```python
def get_secret(short_name: str) -> str:
    """Resuelve un secreto del catalogo.

    En local lee la env var `source_env_var` directa.
    En cloud lee SSM via `target_env_var` (path).
    El nombre corto se mapea a ambos via env vars que devtools inyecta:
    'SSM_<UPPER>_PATH' (cloud) y '<SOURCE_ENV_VAR>' (local).
    """
    # Conversion convencional: 'neon-url' -> ('SSM_NEON_URL_PATH', leer source via catalog)
    # Mejor: devtools inyecta tambien un dict de mapeo via env CATALOG_<NAME>=...
    ...
```

→ La forma exacta del helper se decide en implementación. Lo que importa
es el invariante: **el helper SIEMPRE devuelve el valor del secreto;
internamente decide la fuente según las env vars presentes**.

## Cambio mínimo en código existente

Hoy las Lambdas leen SSM en código como:

```python
# serverless/lambda/services/contact_form/core/services/turnstile.py (ejemplo)
def get_turnstile_secret() -> str:
    path = os.environ['SSM_TURNSTILE_SECRET_PATH']
    response = ssm_client.get_parameter(Name=path, WithDecryption=True)
    return response['Parameter']['Value']
```

Se convierte en:

```python
from shared.aws.ssm import get_secret

def get_turnstile_secret() -> str:
    return get_secret('turnstile-secret')
```

El helper `get_secret` está en `shared/aws/ssm/` y se vendoriza al deploy
(ya lo hace `shared_resolver.py`).

## Archivos afectados

### Crear

- `serverless/lambda/shared/aws/ssm/secret_resolver.py` — helper `get_secret`
  - Verificar: tests unit con env vars stub
- `devtools/serverless/local_runtime_secrets.py` — `_build_local_env`
  - Verificar: tests unit con fixture `.local`

### Modificar

- `devtools/serverless/local_runtime.py` — usar `_build_local_env`
  - Verificar: `serverless run --stage=local --lambda=contact_form` arranca
- `serverless/lambda/services/contact_form/core/services/turnstile.py` —
  reemplazar lectura SSM por `get_secret('turnstile-secret')`
  - Verificar: tests unit del lambda pasan
- `serverless/lambda/services/contact_form/core/services/notification.py` —
  idem para `owner-email`, `ses-from-address`, `ses-from-name`
  - Verificar: tests unit pasan
- `serverless/lambda/services/stream_processor/core/services/neon_writer.py` —
  idem para `neon-url`
  - Verificar: tests unit pasan
- `serverless/lambda/services/db/core/services/migrator.py` — idem para `neon-url`
  - Verificar: tests unit pasan

## Tests TDD

| Test | Cubre AC |
|------|----------|
| `test_get_secret_when_local_source_env_present_returns_value` | AC-7 |
| `test_get_secret_when_cloud_ssm_path_set_calls_ssm` | AC-3 |
| `test_build_local_env_includes_used_secrets_only` | AC-7 |
| `test_build_local_env_when_required_secret_missing_in_dotenv_raises` | AC-6 |
| `test_local_run_no_aws_calls_made` | AC-7 |

## Verify-before-done

```bash
# 1. Tests unit del helper
pytest serverless/lambda/shared/tests/unit/aws/test_secret_resolver.py -v

# 2. Tests del local_runtime
pytest devtools/tests/serverless/test_local_runtime_secrets.py -v

# 3. E2E local del contact_form
python devtools/run.py serverless run --stage=local \
  --lambda=contact_form --event=events/sample.json

# Esperado: la lambda corre, lee TURNSTILE_SECRET_KEY del .local, NO toca AWS
# Verificar con --debug que no hay llamada a boto3.client('ssm')
```
