# Plan: refactor E2E unificado (`e2e` Python, modular por `--module`)

> Unifica los DOS sistemas E2E del portfolio (el harness Python `api_e2e`
> + la suite Playwright TypeScript `tests/feature/`) en UN solo comando
> Python 3.14: `python devtools/run.py e2e --module=<api|admin|app>`.
> Todo corre contra el entorno DESPLEGADO (dev/stage), con herramientas
> compartidas en `tests/shared/`. Elimina `api_e2e`, el modulo `feature`
> de `test_runner` y la carpeta `tests/feature/`.

Plan **Large** (11+ archivos nuevos + ~20 modificados/eliminados).
Sigue [.claude/rules/plan-format.md](../../../.claude/rules/plan-format.md).

## Estado del repo al planificar

- Rama base: `dev` (protegida). Implementar en `feature/e2e-refactor`.
- HEAD: `3787e182` (working tree limpio al planificar).

## Indice navegable

| Archivo | Contenido | Cuando leer |
|---------|-----------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Secciones 1-3: contexto, solucion, criterios de aceptacion (AC) | Entender el porque y el contrato |
| [02-arquitectura-tests.md](02-arquitectura-tests.md) | Estructura final `tests/` + `tests/shared/` + flujo de datos (secciones 4-5) | Antes de tocar `tests/` |
| [03-fase-shared.md](03-fase-shared.md) | Fase A: `tests/shared/` (db, secrets, http, browser, reporter) | Implementar la base compartida |
| [04-fase-comando-e2e.md](04-fase-comando-e2e.md) | Fase B: comando `devtools/e2e/` + container Docker `e2e` | Implementar el orquestador |
| [05-fase-modulo-api.md](05-fase-modulo-api.md) | Fase C: `tests/api/` (porta `api_e2e` flows) | Implementar el modulo api |
| [06-fase-modulo-admin.md](06-fase-modulo-admin.md) | Fase D: `tests/admin/` (flujos browser completos) | Implementar el modulo admin |
| [07-fase-modulo-app.md](07-fase-modulo-app.md) | Fase E: `tests/app/` (smoke+navbar+contact+tracking+screenshots) | Implementar el modulo app |
| [08-fase-eliminacion.md](08-fase-eliminacion.md) | Fase F: borrar `api_e2e` + `feature` + `tests/feature/` + callers | Limpieza de los sistemas viejos |
| [09-fase-rule-skill.md](09-fase-rule-skill.md) | Fase G: rule `.claude/rules/e2e-testing.md` + skill `e2e-testing` | Documentar las reglas en Claude Code |
| [10-tests-requeridos.md](10-tests-requeridos.md) | Seccion 6: tests del comando (devtools unit) + verificacion E2E real | Antes de marcar fases done |
| [11-archivos-afectados.md](11-archivos-afectados.md) | Seccion 7: crear/modificar/eliminar con verificacion por archivo | Checklist ejecutable |
| [12-descomposicion-paralelizacion.md](12-descomposicion-paralelizacion.md) | Seccion 8: tareas atomicas + primitiva de orquestacion | Paralelizar la ejecucion |
| [13-commits.md](13-commits.md) | Seccion 9: commits incrementales (Conventional Commits ES) | Ejecutar commit a commit |
| [14-paralelizacion-worktrees.md](14-paralelizacion-worktrees.md) | Seccion 10: base secuencial + olas worktree-safe | Lanzar worktrees |
| [15-verificacion-e2e.md](15-verificacion-e2e.md) | Seccion 11: bateria final + verificacion real (Partes A/B/C) | Gate de cierre del plan |
| [16-definition-of-done.md](16-definition-of-done.md) | Seccion 12: checklists pre-impl + DoD | Validar cierre |

## Decisiones no reabribles (acordadas en Q&A)

1. **Runtime unico Python 3.14**: TODOS los E2E en Python. Browser via
   `playwright` (python). API via `httpx`. DB via `psycopg`. NO se mantiene
   ningun spec TypeScript/Playwright.
2. **Reusar `devtools/.venv`**: los tests E2E corren bajo el entorno
   Python 3.14 de devtools. Las deps E2E (`playwright`, `pytest`,
   `httpx`, `psycopg`) se agregan a `devtools/pyproject.toml`.
3. **Solo entorno DESPLEGADO (dev/stage)**: NO mas stack Docker local
   (nginx + 6 apps) para los E2E. `app`/`admin` navegan las URLs publicas
   `{niche}.portfolio.{env}.the-full-stack.com`. NUNCA prod.
4. **3 modulos first-class**: `api` (Lambdas HTTP, todos los casos),
   `admin` (flujos completos: login/logout/forms/MFA), `app` (las 6 apps
   Astro: smoke+navbar+contact+tracking+screenshots).
5. **`tests/shared/`**: db (Neon seed+cleanup), secrets (bypass+SSM+admin
   whitelist), http (cliente+IpRotator+emails+reporter), browser
   (playwright-python harness: navegar, click, llenar, login/logout).
6. **Auth admin real**: bypass Turnstile + seed Neon -> flujos end-to-end
   100% reales (no inyeccion de tokens en localStorage).
7. **Container Docker `e2e` dedicado**: Python 3.14 + `.venv` + playwright
   browsers preinstalados. `e2e` lo levanta on-demand. `api` puede correr
   sin browser (httpx puro).
8. **Eliminar `api_e2e` + `feature`**: `e2e` es la UNICA fuente de verdad.
   Se borra `devtools/api_e2e/`, el modulo `feature` de `test_runner` y la
   carpeta `tests/feature/`. Actualizar pre-push hook, CI, CLAUDE.md,
   rules y memory.
9. **Screenshots portados a `app`**: `cv-screenshots` migra a
   playwright-python (PNG en `tests/results/`, gitignored).
10. **Fallar duro sin auth**: `e2e --module=api|admin` exige SSO + clave
    privada Ed25519 local; si falta -> exit error (NO skip-graceful).
    (El modulo `app` no-auth puede correr sin credenciales.)
11. **Documentar en rule + skill**: nueva rule `.claude/rules/e2e-testing.md`
    + skill `e2e-testing` con las reglas de esta arquitectura.

## Reglas criticas del plan

- SIEMPRE Python 3.14 (`devtools/.venv`), NUNCA TypeScript en E2E nuevos.
- SIEMPRE contra dev/stage desplegado, NUNCA prod, NUNCA stack Docker local.
- SIEMPRE hermetico: ningun valor de secreto (bypass, Neon URL) a stdout.
- SIEMPRE `rm -f` para eliminar; temporales en `./tmp/`.
- NUNCA atribucion de IA en commits/PRs.
- El ultimo commit elimina `docs/specs/e2e-refactor/` (carpeta efimera).

## Matriz de verificacion (resumen)

| Fase | Verificacion incremental |
|------|--------------------------|
| A shared | `pytest devtools/tests/unit/src/e2e_shared/` + import OK |
| B comando | `python devtools/run.py e2e --help`; container `e2e` build OK |
| C api | `e2e --module=api --env=dev` PASS (== cobertura api_e2e) |
| D admin | `e2e --module=admin --env=dev` PASS (flujos browser reales) |
| E app | `e2e --module=app --env=dev` PASS (6 apps) |
| F elimina | `rg -l "api_e2e\|tests/feature\|module=feature"` cero hits funcionales |
| G rule/skill | `claude -p` valida la skill (5 angulos, ver claude-config-testing.md) |
| H final | bateria seccion 11 verde + curl real + `e2e` los 3 modulos verdes |
