# 01 — Contexto, solucion y criterios de aceptacion

[<- README](README.md) | [Siguiente: 02 arquitectura ->](02-arquitectura-tests.md)

## 1. Contexto / Problema

El portfolio tiene HOY **dos sistemas E2E desacoplados, en dos lenguajes**:

1. **`devtools/api_e2e/`** (Python 3.14, 16 archivos). Harness HTTP real
   contra el backend **desplegado** (dev/stage). Prueba los 5 Lambdas HTTP
   (cv, contact_form, tracking_pixel, auth, users) con flujos de exito +
   error. Maquinaria propia: conexion Neon via SSM (`environment.py`),
   bypass Turnstile firmado Ed25519, seed/cleanup de DB, `IpRotator`,
   reporter de tiempos, generador TOTP. Comando:
   `python devtools/run.py api_e2e --env=dev`.

2. **`tests/feature/`** (TypeScript + Playwright, 11 specs). Navegador
   contra las 6 apps Astro + admin Next.js via el **stack Docker local**
   (nginx, puerto 9970). Specs en `admin/` (7), `contact/` (2), `navbar/`
   (1), `tracking/` (2), `smoke/` (4). Container `feature` con chromium +
   webkit. Comando: `python devtools/run.py test_runner --module=feature
   --type=feature`.

### Problemas

- **Dos lenguajes, dos runners, dos mentales**: api_e2e (Python/HTTP) y
  feature (TS/Playwright) duplican conceptos (bypass token, datos
  sinteticos, helpers de subdominio) en stacks distintos.
- **Naming inconsistente**: `api_e2e` mezcla "api" + "e2e" en el nombre;
  `feature` es una carpeta semanticamente vacia (`tests/feature/` no
  agrega informacion: TODO ahi dentro es un feature).
- **Dependencia del stack Docker local** para la suite Playwright: lenta
  de levantar, requiere nginx + 6 apps + container feature.
- **No hay un solo punto de entrada** para "corre los E2E del modulo X".

### Hallazgos de exploracion

- `api_e2e` ya prueba TODO el dominio auth + dashboard contra dev (75 casos
  PASS segun memory). Su maquinaria (Neon, bypass, cleanup) es reutilizable.
- La MAYORIA de specs de `tests/feature` (smoke, navbar, contact-validation,
  tracking-intercept) **NO mutan datos**: navegan e interceptan `/track`
  con `page.route`, o validan UI client-side (Zod, redirecciones). Eso
  funciona identico contra dev/stage desplegado. Solo admin/01-login y
  admin/02-register tocan el backend real (auth + bypass).
- Los scripts de devtools se descubren por convencion: una carpeta con
  `main.py` bajo `devtools/` se registra sola en `run.py`
  (`discover_valid_scripts`). Crear `devtools/e2e/` lo registra solo.
- Referencias a barrer al eliminar: CLAUDE.md, pre-push hook
  (`.git-hooks/`), CI (`.github/workflows/ci.yml`), docker-compose (servicio
  `feature` en local/dev/test/prod.yml), dockerfiles `feature`,
  `devtools/test_runner/{flags,feature,full_suites}.py`,
  `devtools/tests/unit/src/api_e2e/` + `.../test_runner/`,
  `devtools/shared/{commands,paths,classification,compose}.py`,
  `packages/ui/src/components/ContactFormReact.tsx` (deuda del header viejo).

## 2. Solucion Propuesta

UN comando Python: **`python devtools/run.py e2e --module=<api|admin|app>
--env=<dev|stage>`**. Reglas:

- `devtools/e2e/` (orquestador Python, monocommand con `--module`): resuelve
  secretos, levanta el container `e2e` si el modulo necesita browser, corre
  `pytest tests/<module>/` con la config compartida, reporta tiempos +
  pass/fail. Reusa la estructura de `api_e2e` (flags, config, reporter).
- **`tests/`** se reorganiza en modulos por dominio:
  - `tests/shared/` — herramientas compartidas (DB, secrets, http, browser,
    reporter). Python, importable por los modulos.
  - `tests/api/` — porta los flows de `api_e2e` (cv, contact_form,
    tracking_pixel, auth, users). HTTP puro (sin browser).
  - `tests/admin/` — flujos browser completos del admin (login, register,
    verify, callback, auth-guard, logout, settings, sessions, MFA), reales
    contra dev/stage (bypass + seed Neon).
  - `tests/app/` — las 6 apps Astro: smoke, navbar, contact, tracking,
    screenshots. Browser contra los subdominios desplegados.
- **`tests/feature/` se ELIMINA**. Su contenido se porta a `tests/{admin,app}/`.
- **`devtools/api_e2e/` se ELIMINA**. Su logica se porta a `tests/api/` +
  `tests/shared/`. El comando `e2e --module=api` lo reemplaza.
- **`test_runner --module=feature` se ELIMINA**. Se rechaza con mensaje de
  migracion (patron ya usado para `e2e`/`tests` en mayo 2026).
- **Container Docker `e2e`** (Python 3.14 + `.venv` + playwright browsers):
  `e2e --module=admin|app` lo levanta on-demand. `--module=api` corre sin
  browser (httpx puro, puede ir host o container).

### Decisiones clave

- **Decision 1: runtime Python unico** — elimina la fractura TS/Python; un
  solo lenguaje, un solo conjunto de helpers en `tests/shared/`. La
  maquinaria critica (Neon, bypass, cleanup) ya es Python; portar Playwright
  a `playwright` (python) es lo unico nuevo.
- **Decision 2: contra desplegado dev/stage** — los E2E prueban el sistema
  REAL que sirven los usuarios, no un stack local que puede divergir. Sin
  Docker local (nginx/apps), menos infra que mantener. NUNCA prod (mutan).
- **Decision 3: container `e2e` para browsers** — chromium+webkit (~400 MB)
  no ensucian el host; el container ya es un patron del repo (el `feature`
  actual). `api` no necesita browser.
- **Decision 4: `tests/shared/` como portador unico de herramientas** — DB,
  secrets, http y browser viven una sola vez; `api`/`admin`/`app` los
  importan. Modulariza al maximo (el pedido explicito del usuario).
- **Decision 5: fallar duro sin auth en api/admin** — si esos modulos no
  pueden autenticarse de verdad (sin SSO o sin clave Ed25519 local), NO
  tiene sentido un "PASS" parcial: exit error. `app` (no-auth) corre igual.

## 3. Criterios de Aceptacion (AC)

Formato BDD (Given/When/Then). Fuente de verdad para tests y tareas.

- **AC-1**: Given el entorno desplegado dev con SSO + clave bypass, When
  `python devtools/run.py e2e --module=api --env=dev --aws-profile=tfs-dev`,
  Then corre los flujos de los 5 Lambdas HTTP (== cobertura de `api_e2e`),
  reporta tiempos por caso y exit 0 si todos PASS.
- **AC-2**: Given el mismo entorno, When `e2e --module=admin --env=dev`,
  Then levanta el container `e2e`, abre el browser contra
  `admin.portfolio.dev.the-full-stack.com`, completa flujos REALES (login
  via form + magic-link/code seedeado, register, logout, settings update,
  sessions revoke, MFA TOTP) y exit 0 si PASS.
- **AC-3**: Given el mismo entorno, When `e2e --module=app --env=dev`, Then
  navega los 6 subdominios `{niche}.portfolio.dev.the-full-stack.com`,
  corre smoke + navbar + contact (validacion+funnel) + tracking
  (pageload+payload) + screenshots, y exit 0 si PASS.
- **AC-4**: Given `--module` ausente, When `e2e --env=dev`, Then corre los
  3 modulos en orden (api -> admin -> app) y exit 0 solo si los 3 PASS.
- **AC-5**: Given un valor invalido, When `e2e --module=foo` o `--env=prod`,
  Then exit con error de validacion claro (lista de validos; prod prohibido).
- **AC-6**: Given falta el SSO o la clave privada Ed25519 local, When
  `e2e --module=api` o `--module=admin`, Then exit con error explicito (NO
  skip silencioso). `--module=app` corre igual (no requiere auth).
- **AC-7**: Given el container `e2e`, When un modulo browser corre, Then
  usa Python 3.14 + playwright browsers preinstalados, sin tocar el host.
- **AC-8**: Given `tests/shared/`, When cualquier modulo lo importa, Then
  obtiene DB (Neon seed+cleanup), secrets (bypass+SSM+admin whitelist),
  http (cliente+IpRotator+emails+reporter) y browser (navegar/click/llenar/
  login/logout) sin duplicar logica.
- **AC-9**: Given el harness, When resuelve cualquier secreto (bypass, Neon
  URL), Then NUNCA imprime su valor en stdout/stderr (hermetico, cumple
  `env-files.md`).
- **AC-10**: Given un run que crea datos sinteticos (users/contacts/tracking
  /sessions), When termina (salvo `--keep-data`), Then los borra de Neon +
  limpia las blacklists de IP TEST-NET (best-effort).
- **AC-11**: Given `--samples=N`, When corre un endpoint read-safe, Then
  toma N muestras y reporta cold (por Lambda) + warm (promedio) por caso.
- **AC-12**: Given el refactor completo, When se busca `api_e2e`,
  `tests/feature` o `module=feature` en el repo (codigo funcional), Then no
  hay referencias vivas (solo historicas en git log / planes archivados).
- **AC-13**: Given la nueva rule `.claude/rules/e2e-testing.md` + skill
  `e2e-testing`, When un usuario pregunta como correr/escribir E2E (ES/EN),
  Then la skill se invoca (`num_turns > 1`) y responde con esta arquitectura.

[<- README](README.md) | [Siguiente: 02 arquitectura ->](02-arquitectura-tests.md)
