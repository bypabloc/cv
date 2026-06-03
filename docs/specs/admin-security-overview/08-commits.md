# 08 — Commits (rama `feature/admin-security-overview` desde `dev`)

[<- fase E](07-fase-e-frontend.md) | [Siguiente: verificacion ->](09-verificacion-e2e.md)

> Commits incrementales. Cada uno deja el repo verde (lint + typecheck + tests
> del scope) y ejecuta su verificacion ANTES de commitear. Conventional Commits
> en español. Un solo PR `feature/admin-security-overview -> dev`.

## Orden (por riesgo creciente / dependencias)

1. **`docs(specs): plan seguridad unificada + login fusionado`**
   - Crea `docs/specs/admin-security-overview/` (esta carpeta).
   - Verif: lectura; no toca codigo.

2. **`feat(db): agrega el flag required a los metodos MFA (migration 00000005)`**
   - Migration `00000005_mfa_required_flag.py` + columnas en los 2 modelos.
   - Verif: upgrade+downgrade+upgrade en branch Neon; `serverless tests
     --type=unit --shared`. [AC-B1]

3. **`feat(auth): set-required + enable en repo y services`**
   - Repo: `set_required`, `set_webauthn_required`, `enable_mfa`,
     `enable_webauthn`, `list_required_methods`. Services: `set_required`,
     `enable`, `required_methods`. `mfa.list`/`list_credentials` agregan
     `required`.
   - Verif: `serverless tests --type=unit --shared --lambda=auth`;
     `lint-deps`. [AC-B2, AC-B3, AC-A6]

4. **`feat(auth): controllers set-required y enable (mfa + webauthn)`**
   - `mfa/set_required.py`, `webauthn/set_required.py`, `mfa/enable.py`,
     `webauthn/enable.py`, `webauthn/disable.py` + modelos.
   - Verif: tests de controller. [AC-B2..B4, AC-A6..A10]

5. **`feat(auth): login multi-factor exige los metodos requeridos`**
   - `_mfa_login.py` (required_or_terminal), `verify_password`, `verify_totp`,
     `webauthn/login_verify` (satisfied/required en el temp step=2),
     `recovery_codes_consume` (bypass), `verify_code` (email-emergencia bypass).
   - Verif: tests B5-B9 (multi-required, parcial, recovery, email). [AC-B5..B10]

6. **`refactor(auth): fusiona register en login y elimina la operation register`**
   - `login.start` crea pending; `verify-code`/`verify-magic-link` cierran
     pending->active; borra `controllers/register/` + OPERATIONS entry +
     modelos + tests; consolida email config a `login-unified`.
   - Verif: `serverless tests --type=unit --lambda=auth`; `rg -l register
     core` cero; `seed-email-config` ok. [AC-D1..D9]

7. **`feat(auth): login.check-email expone existencia y metodos disponibles`**
   - `login/check_email.py` + modelo + `login_methods_service`; rate-limit +
     Turnstile.
   - Verif: tests C1-C7. [AC-C1..C7]

8. **`feat(auth): operation security con la action overview agregadora`**
   - `controllers/security/overview.py` + modelo + OPERATIONS entry +
     `list_all`/`counts` en services.
   - Verif: tests A1-A5. [AC-A1..A5]

9. **`feat(admin): panel unificado de seguridad (overview + toggles + requerido)`**
   - api-client + tipos + `useSecurityOverview`/`useToggleMethod`/
     `useSetRequired` + `SecurityOverviewPanel` + page.
   - Verif: `pnpm --filter @portfolio/admin test/typecheck/lint`. [AC-E1..E8]

10. **`feat(admin): login unificado con check-email y elimina la UI de register`**
    - login-form (paso email -> metodos/crear), `use-check-email`, borra
      `register/*` UI + rutas + schema + api-client; nav-item Seguridad.
    - Verif: `pnpm --filter @portfolio/admin build`; `rg -l register
      admin/src` solo refs validas. [AC-E9..E11]

11. **`docs(rules): actualiza auth-system para login unificado + check-email + required`**
    - `.claude/rules/auth-system.md` (anti-enumeration trade-off, sin register,
      required + fallback, nuevas actions). Validar con `claude -p`.
    - Verif: `claude -p` (claude-config-testing.md). [AC-E12]

12. **`test(specs): verificacion E2E + limpieza del plan`**
    - Seccion 11 (Partes A/B/C) + `git rm -r docs/specs/admin-security-overview/`.

## PR

Un solo PR `feature/admin-security-overview -> dev`, merge commit. El body
reusa la bateria de la seccion 11 en "Como probar".

[<- fase E](07-fase-e-frontend.md) | [Siguiente: verificacion ->](09-verificacion-e2e.md)
