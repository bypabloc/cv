# 07 — Verificacion E2E iterativa (fase final)

[<- 06](06-commits.md) | [README](README.md)

Ultima fase + ultimo commit. Tres partes.

## Parte A — refactor de tests

- Ningun test viejo asume 2 invokes de email en register/login/resend (ahora
  1). `rg -n "publish_magic_link|publish_code" serverless/lambda/services/auth/tests`
  -> solo en tests de los metodos legacy, NO en los controllers migrados.
- Ningun test referencia el nav-item `metrics`.
  `rg -n "/metrics" admin/src admin/tests` -> solo `routes.ts` (def) +
  comentarios.

## Parte B — bateria local (repo verde)

```bash
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin test          # bugs 1 + 4
pnpm --filter @portfolio/admin build
ruff check serverless/lambda/shared devtools/serverless
python -m compileall -q serverless/lambda/services/auth/core serverless/lambda/shared
python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless tests --type=unit --lambda=auth     # bug 3
python devtools/run.py serverless tests --type=coverage --lambda=auth # >=80%
python devtools/run.py serverless tests --type=unit --shared          # bug 2 cors
python devtools/run.py test_runner --module=devtools --type=unit      # bug 2 provisioner
```

Bucle: si algo falla -> corregir -> re-ejecutar. No declarar listo con rojo o
coverage <80%.

**Gate de cierre (push + PR)**: solo con Parte A+B verde. `git push` + PR
`-> dev`, esperar 3 checks CI verdes, merge con `--merge`.

## Parte C — despliegue REAL (post-merge, OBLIGATORIA)

El merge a `dev` dispara `deploy-backend.yml` + `deploy-apps.yml`. Esperar los
runs (`gh run watch`).

### 1. Bug 2 (CORS) — reprovision + curl

Reprovisionar el API GW (regenera el MOCK del OPTIONS) + `create-deployment`
del stage. Verificar:

```bash
curl -s -o /dev/null -D - -X OPTIONS \
  -H "Origin: https://admin.portfolio.dev.the-full-stack.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: authorization,content-type" \
  https://api.portfolio.dev.the-full-stack.com/users
```

-> `access-control-allow-headers` debe incluir `Authorization` [AC-6]. Repetir
para `/auth`.

### 2. Bug 3 (email) — seed + redeploy + email real

`serverless seed-email-config --stage=dev` (sube 4 templates + 2 filas)
ANTES/junto al redeploy de `auth`. Disparar `register.start`/`login.start`
real en dev -> llega UN solo email con boton link + code + "expira en 15 min"
[AC-13]. Click al link -> 302 a admin/callback; code en `/verify` -> login OK.

### 3. Bug 1 + 4 (admin) — reload real

Tras `deploy-apps.yml`, abrir
`https://admin.portfolio.dev.the-full-stack.com`, login, **recargar** -> NO
rebota al login (sesion persiste) [AC-1]; el sidebar NO muestra "Metricas"
[AC-12].

No declarar el plan "listo" sin la Parte C verde (curl CORS + email real +
reload real). Bucle de correccion identico a la Parte B.

## Definition of Done

- [ ] AC-1..AC-13 con test (unit) + Parte C (E2E).
- [ ] Coverage per-file >= 80% en archivos modificados (admin + auth).
- [ ] Typecheck + lint + lint-deps limpios.
- [ ] Build estatico del admin OK.
- [ ] CI (3 checks) verde; PR mergeado con `--merge`.
- [ ] Parte C: preflight OPTIONS /users+/auth con `Authorization`; 1 email con
      link+code; reload mantiene sesion; sidebar sin "Metricas".
- [ ] Carpeta `docs/specs/admin-session-cors-email-metrics/` eliminada en el
      ultimo commit.
