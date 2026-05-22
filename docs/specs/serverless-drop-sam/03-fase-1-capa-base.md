# 03 — Fase 1: capa base (`aws_cli.py` + `state.py`)

> [Anterior: 02](02-arquitectura-objetivo.md) | [README](README.md) | [Siguiente: 04](04-fase-2-provisioner-lambda.md)

Capa fundacional sin dependencias de otras fases. Todo lo demas se apoya
aqui. Es la primera y debe ir secuencial (Fases 2, 3, 4 dependen de ella).

## Objetivo

1. `aws_cli.py` — un unico wrapper sobre `subprocess` para invocar
   `aws ...`: inyecta `--profile` / `--region`, parsea JSON, normaliza
   errores. Hoy cada modulo arma su propio `_aws()`
   ([infra_deploy.py:142](../../../devtools/serverless/infra_deploy.py#L142),
   [lambda_controller.py:92](../../../devtools/serverless/lambda_controller.py#L92)).
2. `state.py` — lee, escribe y compara el archivo de estado por
   `(scope, stage)`. Calcula los hashes de config y de codigo.

## Archivos afectados

### Crear

- `devtools/serverless/aws_cli.py` — wrapper AWS CLI.
- `devtools/serverless/state.py` — estado local + diff.
- `serverless/lambda/.state/.gitignore` — contenido: `*.json` + `!.gitignore`.
- `devtools/tests/unit/src/serverless/test_aws_cli.py` — tests del wrapper.
- `devtools/tests/unit/src/serverless/test_state.py` — tests del estado.

### Verificar que no rompe

- `devtools/serverless/infra_deploy.py` — tiene su `_aws()` propio; en
  esta fase NO se toca (se migra en Fase 3). Coexisten.

## `aws_cli.py` — diseno

API publica minima:

```python
class AwsError(RuntimeError):
    """Fallo de un comando aws CLI. Lleva returncode + stderr."""

def aws(
    args: list[str],
    *,
    profile: str | None = None,
    region: str = 'us-east-1',
    parse_json: bool = False,
    check: bool = True,
) -> AwsResult:
    """Ejecuta `aws <args>`. Devuelve AwsResult(returncode, stdout, json, stderr).

    - profile: inyecta --profile si no es None.
    - region: inyecta --region.
    - parse_json: si True, parsea stdout como JSON en .json.
    - check: si True y returncode != 0, lanza AwsError.
    """

def aws_resource_exists(
    service: str, describe_args: list[str], *, profile, region
) -> bool:
    """True si un `aws <service> describe-*` retorna 0. Para idempotencia."""
```

Reglas:

- Todo `subprocess.run` con `capture_output=True, text=True, check=False`;
  el `check` logico lo maneja `aws()`.
- `# noqa: S603` justificado: el comando lo arma devtools (binario fijo
  `aws` + flags derivados), sin input de usuario no confiable.
- Sin estado global. Funciones puras salvo la llamada a subprocess.

## `state.py` — diseno

```python
@dataclass(frozen=True)
class LambdaState:
    scope: str
    stage: str
    config_hash: str
    code_hash: str
    resources: dict[str, str | None]
    updated_at: str

# Enum de la accion que decide el diff:
#   CREATE | UPDATE_CODE | UPDATE_CONFIG | UPDATE_BOTH | NOOP

def state_path(scope: str, stage: str) -> Path:
    """serverless/lambda/.state/<scope>-<stage>.json"""

def load_state(scope: str, stage: str) -> LambdaState | None:
    """Lee el estado; None si no existe (= nunca se deployo)."""

def save_state(state: LambdaState) -> None:
    """Escribe el JSON (crea .state/ si no existe)."""

def clear_state(stage: str) -> list[Path]:
    """Borra todos los .state/*-<stage>.json. Devuelve los borrados."""

def config_hash(rendered_config: dict) -> str:
    """SHA256 estable (json.dumps sort_keys) de la config renderizada."""

def code_hash(code_dir: Path) -> str:
    """SHA256 del contenido de core/ (recorre archivos ordenados)."""

def diff(
    previous: LambdaState | None,
    new_config_hash: str,
    new_code_hash: str,
) -> Action:
    """Decide la accion comparando hashes previos vs nuevos."""
```

Reglas del `diff`:

| previous | config | code | Accion |
|----------|--------|------|--------|
| None | — | — | `CREATE` |
| existe | igual | igual | `NOOP` |
| existe | igual | distinto | `UPDATE_CODE` |
| existe | distinto | igual | `UPDATE_CONFIG` |
| existe | distinto | distinto | `UPDATE_BOTH` |

`code_hash` se calcula sobre `core/` ANTES de vendorizar `shared/` (el
codigo del Lambda, no la libreria comun — la libreria comun afecta el
artefacto pero su cambio se refleja igual en el zip; ver nota en Fase 2
sobre incluir el cierre de `shared/` en el hash).

## Criterios de aceptacion

- **AC-1.1**: Given `aws()` con `profile='tfs-dev'`, When se invoca,
  Then el comando ejecutado incluye `--profile tfs-dev` y `--region`.
- **AC-1.2**: Given un comando aws que falla, When `check=True`, Then
  lanza `AwsError` con `returncode` y `stderr`.
- **AC-1.3**: Given `parse_json=True` y stdout JSON valido, When se
  invoca, Then `AwsResult.json` es el dict parseado.
- **AC-1.4**: Given un `scope`/`stage` sin estado previo, When
  `load_state`, Then retorna `None`.
- **AC-1.5**: Given un `LambdaState`, When `save_state` y luego
  `load_state`, Then el estado leido es igual al guardado.
- **AC-1.6**: Given `previous=None`, When `diff`, Then `Action.CREATE`.
- **AC-1.7**: Given hashes identicos, When `diff`, Then `Action.NOOP`.
- **AC-1.8**: Given solo `code_hash` distinto, When `diff`, Then
  `Action.UPDATE_CODE`.
- **AC-1.9**: Given solo `config_hash` distinto, When `diff`, Then
  `Action.UPDATE_CONFIG`.
- **AC-1.10**: Given dos `core/` con el mismo contenido en distinto
  orden de archivos, When `code_hash`, Then el hash es identico
  (determinismo).
- **AC-1.11**: Given `.state/contact-form-dev.json` y
  `.state/infra-dev.json`, When `clear_state('dev')`, Then ambos se
  borran y `clear_state('stage')` no los toca.

## Tests requeridos (`devtools/tests/unit/src/serverless/`)

`test_aws_cli.py` — `subprocess.run` mockeado:

- `test_aws_when_profile_given_includes_profile_flag` [AC-1.1]
- `test_aws_when_command_fails_and_check_raises_awserror` [AC-1.2]
- `test_aws_when_parse_json_returns_parsed_dict` [AC-1.3]
- `test_aws_resource_exists_when_describe_returns_zero_true`
- `test_aws_resource_exists_when_describe_returns_nonzero_false`

`test_state.py` — filesystem real en `tmp_path`:

- `test_load_state_when_no_file_returns_none` [AC-1.4]
- `test_save_then_load_roundtrip` [AC-1.5]
- `test_diff_when_no_previous_returns_create` [AC-1.6]
- `test_diff_when_hashes_equal_returns_noop` [AC-1.7]
- `test_diff_when_code_changed_returns_update_code` [AC-1.8]
- `test_diff_when_config_changed_returns_update_config` [AC-1.9]
- `test_diff_when_both_changed_returns_update_both`
- `test_code_hash_is_order_independent` [AC-1.10]
- `test_clear_state_only_targets_stage` [AC-1.11]

## Verificacion incremental con comandos devtools

Esta fase agrega modulos nuevos sin tocar el CLI todavia, asi que los
comandos `serverless` que se verifican son los que ya existen y NO deben
romperse:

```bash
# La suite de tests del CLI sigue verde con los modulos nuevos
python devtools/run.py serverless tests --type=unit
python devtools/run.py serverless help                    # el CLI arranca
```

Ambos deben pasar: los modulos nuevos (`aws_cli.py`, `state.py`) no se
importan aun desde el CLI, pero su sola presencia no debe romper la
coleccion de tests ni el arranque del CLI.

## Verificacion (Definition of Done de la fase)

```bash
devtools/.venv/bin/python -m pytest devtools/tests/unit/src/serverless/test_aws_cli.py devtools/tests/unit/src/serverless/test_state.py -v
python devtools/run.py docker lint --module=devtools     # Ruff
devtools/.venv/bin/python -m mypy devtools/serverless/aws_cli.py devtools/serverless/state.py
# comandos devtools que no deben romperse:
python devtools/run.py serverless tests --type=unit
python devtools/run.py serverless help
```

- [ ] AC-1.1..AC-1.11 cubiertos por tests verdes
- [ ] Coverage >= 80% per-file en `aws_cli.py` y `state.py`
- [ ] Ruff + mypy sin errores
- [ ] `serverless/lambda/.state/.gitignore` creado; `git status` no
      muestra `.state/*.json`
- [ ] `serverless tests --type=unit` y `serverless help` siguen verdes

---

[Anterior: 02](02-arquitectura-objetivo.md) | [README](README.md) | [Siguiente: 04](04-fase-2-provisioner-lambda.md)
