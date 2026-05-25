# 03 - Fase auth

> Implementacion de `auth.py` + subcomando `setup`. Maneja
> storageState de Playwright para Ahrefs y Semrush.

[< 02 Scaffold](02-fase-scaffold.md) | [04 Tools >](04-fase-tools.md)

## Alcance

- `devtools/ai_audit/auth.py` con: `load`, `save`, `check`,
  `setup_interactive`.
- Wire del subcomando `setup` en `main.py`.
- `docker/env/dev-cli/ai-audit/` como directorio target (creado on
  demand con perms 700).
- Archivos `.json` con perms 600.

## AC referenciados

- AC-1 (setup --check-only sin storageState retorna MISSING/EXPIRED)
- AC-6 (run sin storageState reporta SKIPPED, no crashea)

## Tareas atomicas

### T-3.1 auth.py contrato

```python
STORAGE_DIR = Path('docker/env/dev-cli/ai-audit')

class AuthState(StrEnum):
    VALID = 'VALID'
    EXPIRED = 'EXPIRED'
    MISSING = 'MISSING'

def storage_path(tool_name: str) -> Path:
    return STORAGE_DIR / f'{tool_name}.json'

def load(tool_name: str) -> dict | None:
    """Devuelve el storageState parseado, o None si no existe."""

def save(tool_name: str, state: dict) -> None:
    """Persiste storageState con perms 600."""

def check(tool_name: str) -> AuthState:
    """Verifica si el archivo existe y tiene cookies (sin abrir browser)."""

async def setup_interactive(tool_name: str, login_url: str) -> None:
    """Abre browser NO-headless, espera login manual, guarda state."""
```

Detalles:

- `check` solo lee el archivo y valida shape (`cookies`, `origins`).
  NO hace red.
- `setup_interactive` usa `chromium.launch(headless=False)` + polling
  cada 2s revisando si la URL contiene `/dashboard` o similar
  (configurable por tool). Tras detectar, llama
  `context.storage_state(path=...)` y cierra browser.
- Para `--check-only`: solo invoca `check(tool_name)` y exit 0 si
  `VALID`, 1 en otro caso.

### T-3.2 Tests auth.py

`test_auth.py` (Playwright mockeado con `unittest.mock`):

- Given un archivo `ahrefs.json` valido, When `check('ahrefs')`, Then retorna `AuthState.VALID` [AC-1]
- Given un archivo `ahrefs.json` con `cookies=[]`, When `check`, Then retorna `AuthState.EXPIRED` [AC-1]
- Given no existe el archivo, When `check`, Then retorna `AuthState.MISSING` [AC-1]
- Given un dict valido, When `save('ahrefs', state)`, Then el archivo se crea con perms 0o600 [AC-1]
- Given `load('ahrefs')` y existe el archivo, When invoca, Then retorna el dict parseado [AC-6]
- Given `load('ahrefs')` y NO existe, When invoca, Then retorna None [AC-6]

### T-3.3 Wire subcomando setup

En `main.py`:

```python
def _run_setup(flags: dict) -> int:
    tool = flags['tool']
    check_only = flags.get('check_only', False)
    if check_only:
        state = auth.check(tool)
        print(state.value)
        return 0 if state == AuthState.VALID else 1
    asyncio.run(auth.setup_interactive(tool, LOGIN_URLS[tool]))
    return 0
```

`LOGIN_URLS` definido en `auth.py`:

```python
LOGIN_URLS = {
    'ahrefs': 'https://app.ahrefs.com/login',
    'semrush': 'https://www.semrush.com/login/',
}
```

### T-3.4 Verificacion smoke

```bash
# Sin storageState:
python devtools/run.py ai_audit setup --tool=ahrefs --check-only
# Esperado: imprime MISSING, exit 1
```

## Done

- [ ] T-3.1 auth.py implementado, type hints OK
- [ ] T-3.2 6 tests pasan, coverage `auth.py` >= 80%
- [ ] T-3.3 subcomando setup wireado
- [ ] T-3.4 smoke `--check-only` retorna MISSING en maquina limpia
- [ ] Commit: `feat(devtools): ai_audit auth + subcomando setup con storageState`

## Anti-patterns

- NO leer storageState con Read tool de Claude (es credencial — ver
  rule `env-files.md`). El script lo carga directo via Playwright.
- NO commitear `docker/env/dev-cli/ai-audit/` (ya gitignored).
- NO loggear el contenido del storageState (cookies = credencial).

[< 02 Scaffold](02-fase-scaffold.md) | [04 Tools >](04-fase-tools.md)
