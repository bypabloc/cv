# 09 — Verificación E2E iterativa (fase final)

[← ejecución](08-ejecucion.md) · [README](README.md)

> Última fase y último commit. Tres partes. NO se declara "listo" sin las
> tres en verde.

## Parte A — refactor de tests

- Ningún test viejo apunta a `/sessions` (ahora `/settings/sessions`):
  `rg -n "/sessions" admin/src admin/tests tests/` → solo el redirect/tab.
- Ningún test asume `bucket: "day"` hardcodeado ni `refetchInterval` en
  analytics: `rg -n "refetchInterval|bucket.*day" admin/src admin/tests`.
- Ningún test referencia los componentes muertos eliminados
  (webauthn-credentials-list, mfa-methods-list, email-code-section):
  `rg -n "WebAuthnCredentialsList|MfaMethodsList|EmailCodeSection" admin/`.
- Los tests del sidebar reflejan el nuevo conteo de items (sin "Seguridad" ni
  "Mis sesiones" separados).
- Backend: ningún test asume `from`/`to` solo-date donde ahora hay datetime
  (los tests retrocompatibles de date-only siguen verdes).

## Parte B — batería local (repo verde)

```bash
# Backend
python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless lint-deps --lambda=users
python devtools/run.py serverless lint-deps --lambda=analytics
python devtools/run.py serverless tests --type=unit --lambda=auth
python devtools/run.py serverless tests --type=coverage --lambda=auth      # >=80%
python devtools/run.py serverless tests --type=unit --lambda=users
python devtools/run.py serverless tests --type=coverage --lambda=users     # >=80%
python devtools/run.py serverless tests --type=unit --lambda=analytics
python devtools/run.py serverless tests --type=coverage --lambda=analytics # >=80%
python devtools/run.py serverless tests --type=unit --shared

# Admin
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin test          # >=80% per-file
pnpm --filter @portfolio/admin build
```

Bucle "no parar hasta verde": ejecutar → si falla, diagnosticar → corregir →
re-ejecutar la suite → repetir. NO se marca completa con un comando fallando,
un test rojo o coverage < 80%.

## Gate de cierre (push + PR)

Solo con Parte A+B en verde: `git push` + PR `feature/admin-account-fixes-metrics
-> dev` (con `/push-pr-merge` o manual), esperar los 3 checks CI verdes,
merge con `--merge --delete-branch`.

## Parte C — despliegue REAL (post-merge, OBLIGATORIA)

El merge a `dev` dispara `deploy-backend.yml` (redeploy auth/users/analytics)
y `deploy-apps.yml` (admin). Tras esperar los runs (`gh run watch`):

### C-1 Backend (curl + bypass token Ed25519)

```bash
TOKEN=$(python devtools/run.py bypass_token mint --env=dev 2>/dev/null | tail -1)
# (obtener un access JWT de un user active de prueba — ver tests/api)

# AC-2 TOTP: setup-totp -> generar code del secret_b32 -> confirm -> 204
# AC-5 profile.get -> has_password presente
# AC-6 status.get -> current_session_id == family_id del JWT
# AC-3/AC-4 timeseries: from/to datetime + bucket=minute -> puntos por minuto
curl -s -X POST https://api.portfolio.dev.the-full-stack.com/analytics \
  -H "Authorization: Bearer <JWT>" -H 'Content-Type: application/json' \
  -d '{"operation":"timeseries","action":"get","from":"2026-06-03T18:00:00Z","to":"2026-06-03T21:00:00Z","bucket":"minute"}'
```

Esperar a que `deploy-backend.yml` termine ANTES del curl (si no, 500 por
deploy en vuelo). Si una migration de analytics fuera necesaria (no lo es:
solo modelos), correrla con la Lambda `db`.

### C-2 Admin (browser, dev real)

Abrir `https://admin.portfolio.dev.the-full-stack.com`, login, y verificar:
- `/settings`, `/settings/security`, `/settings/sessions` → 200, tab activo
  correcto [AC-8].
- "Nombre para mostrar" editable (tipear funciona) [AC-11].
- Sesiones muestra usuario + sesión actual no vacíos [AC-10].
- Panel seguridad sin email-code [AC-12]; passkey con botón de registro
  funcional [AC-13]; user passwordless ve "Establecer contraseña" sin
  "actual" [AC-14]; change-email envía link al nuevo correo [AC-15].
- TOTP: setup → escanear QR → confirmar con el code → éxito [AC-2].
- `/metrics`: la gráfica de eventos dibuja la línea [AC-16]; retención con
  tooltip [AC-17]; dropdown CloudWatch Relative/Absolute funcional [AC-18,
  AC-19]; sin polling, botón "Actualizar" recarga [AC-20].

```bash
curl -fsS -o /dev/null -w "HTTP %{http_code}\n" --max-time 25 \
  https://admin.portfolio.dev.the-full-stack.com/settings/
curl -fsS -o /dev/null -w "HTTP %{http_code}\n" --max-time 25 \
  https://admin.portfolio.dev.the-full-stack.com/settings/sessions/
```

Bucle de corrección idéntico a la Parte B. El plan NO está "listo" hasta que
la Parte C esté verde (curl backend + browser admin).

## 12. Definition of Done

- [ ] AC-1..AC-20 con test que los cubre y pasa (unit) + Parte C (E2E real).
- [ ] Coverage per-file >= 80% en archivos modificados (auth, users,
      analytics, admin).
- [ ] Typecheck + lint + lint-deps limpios (3 lambdas + admin + shared).
- [ ] Build estático del admin OK.
- [ ] CI (3 checks) verde; PR mergeado a dev con `--merge`.
- [ ] Parte C: TOTP confirm 204; has_password en profile.get;
      current_session_id en status.get; timeseries datetime+minute; tabs de
      settings; display_name editable; panel sin email-code + passkey
      registrable + set-password; /metrics con gráfica + tooltip + dropdown +
      sin polling.
- [ ] Carpeta `docs/specs/admin-account-fixes-metrics/` eliminada en el
      último commit.

[← ejecución](08-ejecucion.md) · [README](README.md)
