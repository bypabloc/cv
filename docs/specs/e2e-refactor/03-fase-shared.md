# 03 — Fase A: `tests/shared/` (base compartida)

[<- 02 arquitectura](02-arquitectura-tests.md) | [Siguiente: 04 comando e2e ->](04-fase-comando-e2e.md)

> Crea el portador unico de herramientas E2E. Es la BASE SECUENCIAL: las
> fases C/D/E dependen de esto. Porta la maquinaria Python de `api_e2e` (sin
> borrarla todavia — la copia, la eliminacion es la fase F) y agrega el
> harness `browser.py` nuevo.

## A.1 — Esqueleto del arbol `tests/`

Crear:

- `tests/pyproject.toml` — config pytest del arbol (markers `api`, `admin`,
  `app`; `testpaths`; `addopts`). NO declara deps (van en
  `devtools/pyproject.toml`).
- `tests/conftest.py` — opciones CLI de pytest (`--env`, `--aws-profile`,
  `--samples`, `--keep-data`, `--lambda`) + fixtures de sesion (Environment,
  HttpClient, Reporter). Estos los inyecta `e2e/main.py` al invocar pytest.
- `tests/shared/__init__.py` (vacio, docstring-only).
- `tests/results/.gitkeep` + agregar `tests/results/` al `.gitignore` raiz.
- `tests/README.md` — apunta a `.claude/rules/e2e-testing.md` (fase G).

## A.2 — Portar la maquinaria de `api_e2e` a `tests/shared/`

COPIAR (no mover; la eliminacion del origen es la fase F) y adaptar imports
`api_e2e.X` -> `tests.shared.X`:

| Nuevo archivo | Origen | Cambios |
|---------------|--------|---------|
| `tests/shared/config.py` | `api_e2e/config.py` | imports; sin cambios de logica |
| `tests/shared/http.py` | `api_e2e/support.py` | renombrar a http; imports |
| `tests/shared/runner.py` | `api_e2e/runner.py` | imports a `tests.shared` |
| `tests/shared/reporter.py` | `api_e2e/reporter.py` | imports |
| `tests/shared/totp.py` | `api_e2e/totp.py` | sin cambios |
| `tests/shared/auth_support.py` | `api_e2e/_auth_support.py` | quitar prefijo `_`; imports |
| `tests/shared/db.py` | `api_e2e/environment.py` (seed/cleanup Neon) | extraer la mitad DB |
| `tests/shared/secrets.py` | `api_e2e/environment.py` (bypass+SSM+admin) | extraer la mitad secrets |

**Split de `environment.py`**: hoy `Environment` mezcla (a) bypass firmado +
SSM + admin whitelist promote/restore y (b) Neon seed + cleanup. Separar en:

- `tests/shared/secrets.py` -> clase `Secrets` (o funciones): `bypass_token()`,
  `_bypass_private_key()`, SSM resolver, `promote_admin()`/`restore_admin()`.
- `tests/shared/db.py` -> clase `Db` (o funciones): `seed_code()`,
  `seed_magic_link()`, `cleanup_users()`, `cleanup_contacts()`,
  `cleanup_tracking()`, `cleanup_rate_limit_blacklist()`.

Mantener un facade `Environment` en `tests/shared/__init__.py` o en un
`tests/shared/environment.py` que componga `Secrets` + `Db` para minimizar
cambios en los flows portados (decidir en C). Hermetismo INTACTO: ningun
valor a stdout (AC-9).

## A.3 — `tests/shared/browser.py` (NUEVO — playwright-python)

Harness de browser que reemplaza `tests/feature/fixtures/index.ts` +
`helpers/*.ts`. API minima (sync o async — preferir **sync** API de
playwright-python por simplicidad con pytest):

```python
# Pseudocodigo de la superficie publica (firmas, no implementacion)
def launch(*, headless: bool = True) -> Browser: ...
def new_page(browser, *, install_bypass: bool = False,
             bypass_token: str | None = None) -> Page: ...
def goto(page, url: str) -> None: ...            # espera load
def click(page, selector: str) -> None: ...
def fill(page, selector: str, value: str) -> None: ...
def wait_selector(page, selector: str, *, state='visible') -> None: ...
def text_of(page, selector: str) -> str: ...
def url_of(page) -> str: ...

# Auth helpers (flujos completos del admin)
def login_via_form(page, *, email, ...) -> None: ...   # llena + submit
def logout(page) -> None: ...

# Tracking helpers (portan disableSendBeacon + captureTrackRequests)
def disable_send_beacon(page) -> None: ...       # addInitScript
def capture_track(page) -> TrackCapturer: ...    # page.route('**/track')

# Bypass (porta installBypass: window.__E2E_BYPASS_TOKEN__)
def install_bypass(page, token: str) -> None: ... # add_init_script

# Screenshots (porta captureScreenshot)
def screenshot(page, *, path: str, full_page: bool = True) -> None: ...
```

Notas de portado:
- `installBypass` -> `page.add_init_script` seteando
  `window.__E2E_BYPASS_TOKEN__`. El admin lo lee y lo manda en
  `X-Turnstile-Bypass-Token`.
- `disableSendBeacon` -> `add_init_script` que sobreescribe
  `navigator.sendBeacon` para forzar el fallback `fetch` (asi playwright ve
  el `postData` del `/track`).
- `captureTrackRequests` -> `page.route('**/track', ...)` acumulando los
  payloads + respondiendo 204 (o dejando pasar segun el test).
- `subdomainUrl(niche)` -> usar `tests/shared/config.py` con las URLs
  DESPLEGADAS (no `localhost:9970`): `{niche}.portfolio.{env}.the-full-stack.com`.

## A.4 — `tests/shared/config.py`: URLs desplegadas (extension)

`api_e2e/config.py` ya tiene `_API_BASE`, `_ADMIN_ORIGIN`, `_CV_ORIGIN`,
`_APEX_ORIGIN`. AGREGAR el mapa de los 6 niches desplegados para `app`:

```python
_NICHE_ORIGIN = {  # patron {niche}.portfolio.{env}.the-full-stack.com
    'dev':   {n: f'https://{n}.portfolio.dev.the-full-stack.com'
              for n in ('hub', 'fintech', 'architect', 'leader', 'vibe')},
    'stage': {...},
}
# generic = apex (the-full-stack.com en prod; en dev/stage usa su subdominio)
```

Confirmar el patron exacto del apex/generic en dev/stage contra
`devtools/cloudflare_setup/config.py` (no asumir). `services.localhost` del
smoke viejo NO tiene equivalente desplegado -> ese sub-caso se DESCARTA o se
reemplaza por un check del apex.

## Verificacion de la fase A

```bash
# 1. Deps E2E instaladas en devtools/.venv (ver fase B para pyproject)
python devtools/run.py --help   # bootstrap uv sync

# 2. Import de cada modulo shared sin error
devtools/.venv/bin/python -c "import sys; sys.path.insert(0,'tests'); \
  import shared.config, shared.http, shared.runner, shared.reporter, \
  shared.totp, shared.auth_support, shared.db, shared.secrets, shared.browser"

# 3. Unit tests del shared portado (los que ya existian para api_e2e,
#    migrados a devtools/tests/unit/src/e2e_shared/)
python devtools/run.py serverless lint-deps  # N/A aqui; usar pytest devtools
devtools/.venv/bin/python -m pytest devtools/tests/unit/src/e2e_shared/ -q
```

## Done de la fase A

- [ ] `tests/{conftest.py,pyproject.toml,README.md}` creados.
- [ ] `tests/shared/*.py` (9 modulos) importan sin error bajo `.venv`.
- [ ] `browser.py` expone la superficie de A.3 (sin specs aun).
- [ ] `config.py` tiene las URLs desplegadas de los 6 niches.
- [ ] Hermetismo verificado (grep del transcript sin valores de secreto).
- [ ] `tests/results/` gitignored.

[<- 02 arquitectura](02-arquitectura-tests.md) | [Siguiente: 04 comando e2e ->](04-fase-comando-e2e.md)
