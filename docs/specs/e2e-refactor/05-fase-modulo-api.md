# 05 — Fase C: `tests/api/` (Lambdas HTTP)

[<- 04 comando e2e](04-fase-comando-e2e.md) | [Siguiente: 06 modulo admin ->](06-fase-modulo-admin.md)

> Porta los flows de `api_e2e` a `tests/api/` como tests pytest. Conserva la
> cobertura EXACTA (los 5 Lambdas HTTP, exito + errores) y el reporte de
> tiempos. HTTP puro (httpx), sin browser. AC-1, AC-10, AC-11.

## C.1 — Decision de portado (Runner imperativo vs pytest puro)

`api_e2e` hoy corre flows imperativos con un `Runner` que toma N samples por
caso y un `Reporter` que arma la tabla de tiempos. Dos opciones:

- **C-A (recomendada, menor riesgo)**: cada flow se convierte en UN
  `test_*` que invoca el flow imperativo existente (ya portado a
  `tests/shared` o a un `tests/api/_flows.py`). El `Runner`/`Reporter`
  siguen siendo la fuente del resumen de tiempos. Pytest aporta
  descubrimiento, `-k`, markers y reporting; el detalle de samples queda
  dentro del flow. Minimiza la reescritura.
- **C-B (mas modular, mas trabajo)**: descomponer cada paso del flow en su
  propio `test_*` con fixtures compartidos (un test por action/escenario).
  Mas granular pero hay que rehacer el encadenamiento de tokens (el access
  token vivo que `auth` pasa a `users`) via fixtures de sesion.

Preferir **C-A** para esta fase (conserva el comportamiento verificado de
api_e2e). Dejar C-B como refactor futuro si se quiere mas granularidad.

## C.2 — Archivos

| Archivo | Porta de | Cobertura |
|---------|----------|-----------|
| `tests/api/conftest.py` | — | fixtures: `environment`, `http`, `runner`, `reporter`, `bypass`, `run_id`, `created_emails/sessions` (cleanup en teardown) |
| `tests/api/test_cv.py` | `flow_readonly.run_cv` | 10 read actions (2xx) + action invalida + sin operation |
| `tests/api/test_contact_form.py` | `flow_readonly.run_contact` | contact.create 202 (bypass) + sin message + email invalido |
| `tests/api/test_tracking_pixel.py` | `flow_readonly.run_tracking` | tracking.track 202 + sin event_type_id + viewport invalido |
| `tests/api/test_auth.py` | `flow_auth.run_auth` | register/login/verify/session (success + errores) |
| `tests/api/test_auth_mfa.py` | `flow_auth_mfa.run_mfa_flows` | TOTP setup/confirm/login-2FA + email-code + recovery |
| `tests/api/test_users.py` | `flow_users.run_users` | profile/status/change-password/change-email/delete-account |
| `tests/api/test_admin.py` | `flow_admin` | admin.* con promote/restore SSM whitelist |

> Si se elige C-A, los cuerpos de `flow_*.py` se mueven a un modulo interno
> `tests/api/_flows.py` (prefijo `_` para que pytest no lo recolecte) o a
> `tests/shared/` y cada `test_*.py` los invoca. Mantener el orden de
> dependencia: `test_auth` produce el access token que `test_users` consume
> (via fixture de sesion `auth_access_token` con scope module/session).

## C.3 — Cadena de tokens auth -> users

El detalle critico (de `flow_auth`): el logout base se hace sobre `access1`
(verify-code), NO sobre `access2` (refresh), para que `access2` siga vivo y
`users` lo reutilice. Esto se preserva con un fixture de sesion que corre
`auth` primero y expone el `access_token` vivo a `users`. Si `--module=api`
corre solo `users` sin `auth`, el fixture debe generar el token (registrar
un user activo) — igual que hoy `main._run_flows` corre `auth` cuando se
pide `users`.

## C.4 — Datos sinteticos + cleanup (AC-10)

- Emails `success+api-e2e-<run>-<slot>@simulator.amazonses.com` (SES
  simulator) — ya en `shared/config.synthetic_email`.
- IP rotada por request (TEST-NET RFC 5737) — `shared/config.IpRotator`.
- Cleanup en el teardown del `conftest.py`: `cleanup_users`,
  `cleanup_contacts`, `cleanup_tracking`, `cleanup_rate_limit_blacklist`
  (de `tests/shared/db.py`). Respeta `--keep-data`.

## C.5 — Seed de Neon (AC-1)

El verify-code y el magic-link necesitan seed (el code/token plano no vuelve
en la respuesta). `tests/shared/db.seed_code()` / `seed_magic_link()`
generan un plaintext conocido, calculan SHA-256 y UPDATEan el hash de la
fila vigente. Hermetico (Neon URL nunca a stdout).

## Verificacion de la fase C

```bash
# Contra dev (requiere SSO + clave bypass; falla duro si falta — AC-6)
python devtools/run.py e2e --module=api --env=dev --aws-profile=tfs-dev

# Un solo Lambda
python devtools/run.py e2e --module=api --lambda=auth --env=dev \
  --aws-profile=tfs-dev

# Comparar cobertura: el resumen debe listar los mismos casos que api_e2e
# (cv, contact_form, tracking_pixel, auth, auth_mfa, users, admin).
```

## Done de la fase C

- [ ] Los 5 Lambdas HTTP cubiertos (cv/contact_form/tracking_pixel/auth/users)
      con exito + errores == cobertura de `api_e2e` (75 casos de referencia).
- [ ] `e2e --module=api --env=dev` exit 0 con todos PASS.
- [ ] Reporte de tiempos (cold por Lambda + warm por caso) presente.
- [ ] Cleanup de datos sinteticos verificado (Neon + blacklist).
- [ ] `--lambda=<X>` filtra a un solo Lambda.
- [ ] Falla duro sin SSO/clave (AC-6).

[<- 04 comando e2e](04-fase-comando-e2e.md) | [Siguiente: 06 modulo admin ->](06-fase-modulo-app.md)
