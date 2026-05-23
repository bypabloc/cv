# Fase 6 — No-leaking + hermetismo

> Garantiza que devtools nunca imprime un valor cargado del `.env`,
> ni en stdout, stderr, logs, exception traceback, ni como argumento
> de subprocess visible en `ps`. Verificado por tests automatizados.

## Inventario de vectores de leak

| Vector | Riesgo | Mitigación |
|--------|--------|------------|
| `print(value)` o `print(env_dict)` | Stdout | Lint rule + tests que asserten no-leak |
| `logger.info(f'X={value}')` | Stdout + archivos de log | Mismo |
| `aws ssm put-parameter --value <X>` | `ps aux` lo expone mientras corre | Usar `--value file://<tmp>` con perms 0600 |
| `subprocess.run([..., '--value', value])` | Idem | Idem |
| `except Exception as e: raise Foo() from e` donde `e.args` contiene el valor | Traceback | `raise Foo() from None` |
| `repr(SecretSpec)` con valor embebido | Cualquier output | `SecretSpec` NO guarda el valor (solo el path/meta) |
| `pdb`, `breakpoint()` en código de prod | Debug accidental | Lint rule `T100` (debugger) ya activo |
| Coredump de Python con el dict env | Disco | Aceptado (out of scope, requiere kernel hardening) |
| `git commit` accidental del `.env` | git history | `.gitignore` cubre `docker/env/server/.{local,dev,stage,prod,test}` |

## Reglas de implementación

### 1. `SecretSpec` no carga valores

`SecretSpec` (dataclass del catálogo) solo guarda METADATA del secreto:
nombre, path, ssm_type, env_var, stages. NUNCA un valor. El valor vive
exclusivamente en un dict local `env_values: dict[str, str]` que pasa
por las funciones de sync y se descarta al terminar.

### 2. `aws ssm put-parameter` via tempfile

```python
def _aws_ssm_put_parameter_secure(
    *,
    name: str,
    value: str,
    ssm_type: str,
    kms_alias: str | None,
    aws_profile: str | None,
    region: str,
) -> None:
    """Llama a aws ssm put-parameter pasando el valor por archivo temporal.

    Razon: `--value <X>` queda visible en `ps aux` durante la ejecucion
    de aws-cli. Usamos `--value file:///tmp/...` con perms 0600.
    """
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(
        mode='w',
        delete=False,
        dir='/tmp',
        prefix='portfolio-ssm-',
        suffix='.tmp',
    ) as tmp:
        os.chmod(tmp.name, 0o600)
        tmp.write(value)
        tmp_path = tmp.name
    try:
        cmd = [
            'aws', 'ssm', 'put-parameter',
            '--name', name,
            '--type', ssm_type,
            '--value', f'file://{tmp_path}',
            '--overwrite',
            '--region', region,
        ]
        if ssm_type == 'SecureString':
            cmd.extend(['--key-id', kms_alias or 'alias/portfolio-lambdas'])
        if aws_profile:
            cmd.extend(['--profile', aws_profile])
        subprocess.run(cmd, check=True, capture_output=True)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass  # ya no existe, ignorar
```

### 3. Lectura SSM con descarte inmediato del valor raw

```python
def _aws_ssm_get_value_hash(
    *, name: str, aws_profile: str | None, region: str,
) -> str | None:
    """Lee SSM y devuelve SOLO el hash del valor (nunca el valor).

    Si el parametro no existe, devuelve None.
    """
    cmd = ['aws', 'ssm', 'get-parameter', '--name', name,
           '--with-decryption', '--region', region]
    if aws_profile:
        cmd.extend(['--profile', aws_profile])
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        if 'ParameterNotFound' in result.stderr:
            return None
        raise SecretsSyncError(
            f'aws ssm get-parameter fallo para {name}: '
            f'returncode={result.returncode}',
        )
    import json
    data = json.loads(result.stdout)
    value = data['Parameter']['Value']
    return _hash_value(value)
    # 'value' sale del scope, no se imprime, no se loggea.
```

### 4. Logs estructurados sin valor

```python
# OK
logger.info('[secrets-sync] %-25s [%s] %s hash=%s',
            spec.name, action, spec.path_for(stage), hash_short)

# PROHIBIDO
logger.info(f'sync {spec.name}={value}')
logger.debug('env=%s', env_values)
```

### 5. Excepciones sin payload del secreto

```python
# OK
raise SecretsSyncError(
    f'{spec.name}: aws ssm put-parameter fallo (returncode={rc})',
)

# PROHIBIDO
raise SecretsSyncError(f'{spec.name} valor={value} fallo') from e
```

### 6. Ruff custom rules (opcional, defense in depth)

Agregar a `devtools/ruff.toml` un check basado en `flake8-printf-formatting`
o un comentario obligatorio cuando se llama a `print()` en módulos de
secretos. Para `devtools/serverless/secrets_*.py`:

- `T201` (print): error en estos módulos (forzar `logger`).

## Tests no-leaking obligatorios

`devtools/tests/serverless/test_no_leaking.py`:

```python
import io
import pytest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

CANARY = 'CANARY_NEVER_LOG_ME_b8a7c2e3f9d1'

@pytest.fixture
def env_with_canary(tmp_path):
    env_file = tmp_path / '.dev'
    env_file.write_text(
        f'TURNSTILE_SECRET_KEY={CANARY}\n'
        f'DB_URL=postgresql://x:{CANARY}@host/db\n'
        f'OWNER_EMAIL=test@example.com\n'
        f'EMAIL_FROM=no-reply@example.com\n'
        f'EMAIL_FROM_NAME=Test\n',
    )
    return env_file


def test_sync_secrets_canary_not_in_stdout(env_with_canary, capsys, monkeypatch):
    """AC-10: canary value never appears in stdout."""
    monkeypatch.setattr('subprocess.run', _stub_aws_run)
    from devtools.serverless.secrets_sync import sync_secrets_to_ssm
    from devtools.serverless.secrets_catalog import Catalog

    sync_secrets_to_ssm(
        stage='dev',
        env_file=env_with_canary,
        catalog=Catalog.load(),
        aws_profile=None,
    )
    captured = capsys.readouterr()
    assert CANARY not in captured.out
    assert CANARY not in captured.err


def test_subprocess_args_never_contain_canary(env_with_canary, monkeypatch):
    """AC-10: el valor nunca aparece como argumento de aws-cli."""
    captured_calls = []

    def _capture(cmd, *args, **kwargs):
        captured_calls.append(cmd)
        return _stub_aws_result()

    monkeypatch.setattr('subprocess.run', _capture)
    from devtools.serverless.secrets_sync import sync_secrets_to_ssm
    from devtools.serverless.secrets_catalog import Catalog

    sync_secrets_to_ssm(
        stage='dev', env_file=env_with_canary,
        catalog=Catalog.load(), aws_profile=None,
    )
    for call in captured_calls:
        joined = ' '.join(str(x) for x in call)
        assert CANARY not in joined, (
            f'canary leaked into subprocess args: {call}'
        )


def test_exception_traceback_no_canary(env_with_canary, monkeypatch):
    """AC-10: si algo falla, el traceback no contiene el valor."""
    def _fail(*a, **k):
        raise RuntimeError('simulated failure')
    monkeypatch.setattr('subprocess.run', _fail)
    from devtools.serverless.secrets_sync import sync_secrets_to_ssm
    from devtools.serverless.secrets_catalog import Catalog

    import traceback
    try:
        sync_secrets_to_ssm(
            stage='dev', env_file=env_with_canary,
            catalog=Catalog.load(), aws_profile=None,
        )
    except Exception:
        tb = traceback.format_exc()
        assert CANARY not in tb


def test_secret_spec_repr_no_value(env_with_canary):
    """SecretSpec.repr no incluye ningun valor."""
    from devtools.serverless.secrets_catalog import Catalog
    catalog = Catalog.load()
    for spec in catalog.by_name.values():
        rep = repr(spec)
        assert CANARY not in rep
```

## Pre-commit hook (defense in depth)

Agregar a `.git-hooks/pre-commit` un check rápido: si se modificó
`docker/env/server/.{stage}`, hacer `git diff --cached` y verificar que
NINGUNA línea contiene el patrón `# DEBUG` que podría indicar
"comentario con el valor copy-pasted". Y bloquear si se intenta commitear
`docker/env/server/.{stage}` (que ya están en `.gitignore`, pero defense
in depth).

## Archivos afectados

### Crear

- `devtools/tests/serverless/test_no_leaking.py` — suite hermetismo
  - Verificar: `pytest devtools/tests/serverless/test_no_leaking.py -v`

### Modificar

- `devtools/serverless/secrets_sync.py` — `_aws_ssm_put_parameter_secure`
  con tempfile
  - Verificar: tests no-leaking verdes + manual `ps aux` durante el deploy
- `devtools/ruff.toml` — `T201` error en `secrets_*.py`
  - Verificar: ruff falla si se agrega `print()` en estos módulos
- `.git-hooks/pre-commit` — bloquear commit de `docker/env/server/.{stage}`
  - Verificar: intentar `git add docker/env/server/.dev` falla

## Verify-before-done

```bash
# Tests hermetismo
pytest devtools/tests/serverless/test_no_leaking.py -v

# Defense in depth: ruff
ruff check devtools/serverless/secrets_sync.py
ruff check devtools/serverless/secrets_commands.py

# Verificar a mano que `ps aux` durante un sync NO muestra el valor
# (correr en una terminal mientras se hace deploy en otra)
watch -n 0.1 'ps aux | grep "ssm put-parameter" | grep -v grep'
# Esperado: --value file:///tmp/portfolio-ssm-XXX.tmp (no el valor)
```
