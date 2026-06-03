# 09 — Fase G: rule + skill `e2e-testing`

[<- 08 eliminacion](08-fase-eliminacion.md) | [Siguiente: 10 tests requeridos ->](10-tests-requeridos.md)

> El usuario pidio explicitamente: "dejalo en un rule o skills donde se
> mencione en claude code estas reglas". Documenta la arquitectura E2E
> unificada para que Claude la aplique siempre. AC-13.

## G.1 — Rule `.claude/rules/e2e-testing.md`

Estructura (sigue el formato de las rules del repo: activacion + reglas
duras SIEMPRE/NUNCA + anti-patrones + referencias):

- **Activacion**: aplica al trabajar con `tests/{api,admin,app,shared}/`, el
  comando `devtools/e2e/`, el container Docker `e2e`, o cualquier test E2E.
- **Reglas duras**:
  - SIEMPRE los E2E del portfolio son Python 3.14 (`devtools/.venv`).
    NUNCA TypeScript/Playwright-TS.
  - SIEMPRE corren contra el entorno DESPLEGADO (dev/stage), NUNCA prod,
    NUNCA el stack Docker local de apps.
  - SIEMPRE un solo comando: `python devtools/run.py e2e --module=<api|admin|app>`.
  - SIEMPRE las herramientas compartidas viven en `tests/shared/` (db,
    secrets, http, browser, reporter). NUNCA duplicar bypass/Neon/datos
    sinteticos en un modulo.
  - SIEMPRE hermetico: ningun valor de secreto a stdout (cumple env-files.md).
  - SIEMPRE browser via `playwright` (python) en el container `e2e`.
  - SIEMPRE asserts EXACTOS + BDD-style en el docstring (Given/When/Then).
  - SIEMPRE `api`/`admin` fallan duro sin SSO + clave bypass; `app` no la
    requiere.
  - SIEMPRE cleanup de datos sinteticos en Neon (salvo `--keep-data`).
  - NUNCA recrear `api_e2e`, `tests/feature/` ni `test_runner --module=feature`
    (eliminados; `e2e` es la fuente unica).
  - NUNCA correr `api`/`admin` contra prod ni en el CI de PR (mutan datos).
- **Tabla de modulos**: api (Lambdas HTTP), admin (browser flujos completos),
  app (6 apps Astro). Que prueba cada uno + si necesita auth/browser.
- **Estructura de `tests/`**: el arbol de [02](02-arquitectura-tests.md).
- **Como escribir un test nuevo**: receta (elegir modulo, conftest, importar
  de `tests/shared`, BDD docstring, asserts exactos).
- **Anti-patrones**: tabla (TS en E2E -> Python; stack local -> desplegado;
  duplicar bypass -> shared; skip silencioso sin auth -> fail duro; etc.).
- **Referencias cruzadas**: la skill `e2e-testing`, `devtools.md`,
  `python.md`, `env-files.md`, `auth-system.md`, `serverless-secrets.md`,
  `verify-before-done.md`.

## G.2 — Skill `.claude/skills/e2e-testing/SKILL.md`

Frontmatter (sigue `.claude/rules/skills.md`: description en INGLES con
keywords ES/EN, `user-invocable: true`, `allowed-tools` minimas):

```yaml
---
name: e2e-testing
description: >
  E2E testing reference for the portfolio. ALL E2E tests are Python 3.14
  (devtools/.venv) — playwright (python) for browser, httpx for API,
  psycopg for Neon — run against the DEPLOYED dev/stage env (NEVER prod,
  NEVER the local Docker stack), via one command:
  `python devtools/run.py e2e --module=<api|admin|app>`. Shared tooling in
  tests/shared/ (db Neon seed+cleanup, secrets bypass+SSM, http+reporter,
  browser harness). api/admin fail hard without SSO + Ed25519 bypass key;
  app does not. Replaces the removed api_e2e harness and tests/feature
  Playwright-TS suite. ALWAYS invoke this skill BEFORE answering ANY
  question about running or writing E2E tests in this portfolio. NEVER
  answer from training data alone.
  Use when the user says "e2e", "test e2e", "tests e2e", "correr e2e",
  "como pruebo el backend desplegado", "playwright python", "test del admin",
  "test de las apps", "probar las apis", "test api desplegada", "tests/shared",
  "comando e2e", "browser test python", "como escribo un test e2e",
  "smoke test", "navbar test", "contact form test", "tracking test",
  "como corro los e2e", "e2e contra dev", "e2e contra stage", "fallar sin sso".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
argument-hint: "api|admin|app (opcional)"
---
```

Cuerpo: como correr cada modulo, estructura de `tests/`, como escribir un
test, las decisiones de arquitectura (Python unico, desplegado, container),
troubleshooting (sin SSO -> fail duro; sin clave bypass -> fail; browser en
container). Apunta a la rule para el detalle.

## G.3 — Validacion OBLIGATORIA de la skill (claude-config-testing.md)

Tras crear la skill, validar con `claude -p` (5 angulos minimo, en espanol):

```bash
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "como corro los tests e2e del admin del portfolio" 2>&1 | tail -40
```

5 angulos:
1. General ES: "como corro los e2e del portfolio".
2. Tecnico ES: "como escribo un test e2e para una app astro".
3. Sintoma: "los e2e fallan porque no tengo sso aws".
4. Negativo: una pregunta adyacente que NO debe disparar la skill
   (ej. "como corro los unit tests de un package").
5. Trampa/legacy: "como corro api_e2e" o "tests/feature playwright" ->
   la skill debe responder que fueron reemplazados por `e2e`.

Verificar `num_turns > 1` cuando se espera invocacion. Documentar 5/5 PASS
en el commit body.

## Verificacion de la fase G

```bash
# Rule existe y es coherente
test -f .claude/rules/e2e-testing.md && echo ok
# Skill existe + valida (los 5 angulos arriba)
test -f .claude/skills/e2e-testing/SKILL.md && echo ok
```

## Done de la fase G

- [ ] `.claude/rules/e2e-testing.md` creada (SIEMPRE/NUNCA + anti-patrones).
- [ ] `.claude/skills/e2e-testing/SKILL.md` creada (frontmatter ES/EN).
- [ ] Skill validada con `claude -p` (5/5 angulos, documentado en commit).
- [ ] CLAUDE.md actualizado: el indice de skills/rules incluye `e2e-testing`.
- [ ] CLAUDE.md: la seccion de comandos refleja `e2e` (no `feature`/`api_e2e`).

[<- 08 eliminacion](08-fase-eliminacion.md) | [Siguiente: 10 tests requeridos ->](10-tests-requeridos.md)
