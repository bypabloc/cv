# 13 — Seccion 9: Commits

[<- 12 descomposicion](12-descomposicion-paralelizacion.md) | [Siguiente: 14 worktrees ->](14-paralelizacion-worktrees.md)

> Commits incrementales en Conventional Commits ESPAÑOL. Cada commit deja el
> repo verde (lint + typecheck + tests del scope) y ejecuta su verificacion
> ANTES de commitear. Rama: `feature/e2e-refactor` (de `dev`). Un solo PR
> `feature/e2e-refactor -> dev`. SIN atribucion de IA.

## Secuencia de commits

1. **`docs(specs): plan refactor e2e unificado (python, modular)`**
   - La carpeta `docs/specs/e2e-refactor/` (este plan).
   - Verify: archivos `.md` < 300 lineas; links internos validos.

2. **`chore(devtools): agrega deps e2e (playwright, pytest) a devtools`**
   - `devtools/pyproject.toml` + `uv.lock`; `.gitignore` (tests/results).
   - Verify: `uv sync` OK; `playwright` importable bajo `.venv`.

3. **`test(shared): porta maquinaria e2e a tests/shared + browser harness`**
   - `tests/shared/*` (config, db, secrets, http, runner, reporter, totp,
     auth_support, browser), `tests/{conftest,pyproject,README}`.
   - Migra los unit tests a `devtools/tests/unit/src/e2e_shared/`.
   - AC-8, AC-9. Verify: imports OK + `test_runner --module=devtools --type=unit`
     verde (config/reporter/runner/totp/secrets-hermetic).

4. **`feat(devtools): comando e2e (orquestador) + container docker e2e`**
   - `devtools/e2e/*`, dockerfiles/compose/entrypoint `e2e`, unit tests del
     comando (`e2e/test_flags`, `test_describe`).
   - AC-4, AC-5, AC-6, AC-7. Verify: `e2e --help`; `--module=foo`/`--env=prod`
     error; container build + ready; unit verde.

5. **`test(api): porta los flujos api_e2e a tests/api`**
   - `tests/api/*` (cv, contact_form, tracking_pixel, auth, auth_mfa, users,
     admin).
   - AC-1, AC-10, AC-11. Verify: `e2e --module=api --env=dev --aws-profile=tfs-dev`
     PASS (== cobertura api_e2e).

6. **`test(admin): flujos browser completos del admin (playwright python)`**
   - `tests/admin/*` (login/register/verify/callback/auth-guard/logout/
     settings/sessions/mfa).
   - AC-2. Verify: `e2e --module=admin --env=dev` PASS.

7. **`test(app): porta smoke+navbar+contact+tracking+screenshots a tests/app`**
   - `tests/app/*` (smoke, hub_links, cv_filters, navbar, contact_form,
     contact_funnel, tracking_pageload, tracking_payload, screenshots).
   - AC-3. Verify: `e2e --module=app --env=dev` PASS; PNG en tests/results.

8. **`refactor(devtools): elimina api_e2e + modulo feature + tests/feature`**
   - `git rm` api_e2e, tests/feature, test_runner/feature.py, dockerfiles/
     compose/entrypoint feature; actualiza flags/full_suites/README de
     test_runner; pre-push hook + config.json; CLAUDE.md; refs residuales
     (ContactFormReact, crypto docstrings, READMEs).
   - AC-12. Verify: `rg` sin refs vivas; `test_runner --module=feature`
     rechazado; `test_runner --module=devtools --type=unit` verde;
     `docker compose config` sin servicio feature.

9. **`docs(rules): rule + skill e2e-testing (arquitectura unificada)`**
   - `.claude/rules/e2e-testing.md`, `.claude/skills/e2e-testing/SKILL.md`,
     CLAUDE.md (index skills/rules).
   - AC-13. Verify: `claude -p` 5/5 angulos (documentar en el commit body).

10. **`test(e2e): verificacion E2E iterativa + elimina la carpeta del plan`**
    - Ajustes finales de tests tras la bateria completa.
    - `git rm -r docs/specs/e2e-refactor/` (carpeta efimera).
    - Verify: bateria seccion 11 (Partes A+B) verde; los 3 modulos de `e2e`
      verdes contra dev.

## Regla por commit

- Cada commit corre SU verificacion ANTES de commitear (no se difiere).
- Ningun commit deja el repo en rojo.
- Los commits 5/6/7 (los modulos E2E) requieren SSO + clave bypass para
  verificar contra dev; si no hay credenciales en el momento del commit, el
  commit se hace con la verificacion estatica (imports/lint/collect-only) y
  la verificacion contra dev se consolida en el commit 10 (seccion 11).

## PR

- Un solo PR `feature/e2e-refactor -> dev`, merge commit.
- Body: 4 secciones (Problema / Solucion / Como probar / TODO).
- "Como probar" = la bateria de la seccion 11.
- Gate de cierre: push + PR SOLO con la seccion 11 (Partes A+B) verde.

[<- 12 descomposicion](12-descomposicion-paralelizacion.md) | [Siguiente: 14 worktrees ->](14-paralelizacion-worktrees.md)
