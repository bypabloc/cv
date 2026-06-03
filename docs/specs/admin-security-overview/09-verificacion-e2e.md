# 09 — Verificacion E2E iterativa (fase final)

[<- commits](08-commits.md) | [README ->](README.md)

> Ultima fase y ultimo commit. Tres partes. Bucle "no parar hasta que funcione":
> ejecutar -> si falla, diagnosticar -> corregir -> re-ejecutar -> repetir.
> Cubre AC-Z1..AC-Z4.

## 8 — Descomposicion / paralelizacion

Secuencial inline en el orden de commits (B -> D -> C -> A -> E). Los archivos
del backend (auth/core) y del frontend (admin/src) son disjuntos POR FASE, pero
las fases dependen entre si (B bloquea D/A; D bloquea C; A consume todo). NO se
paraleliza con worktrees: el riesgo (modelo + login + migration) exige orden
estricto. Los tests corren en Bash/devtools, NO con 1 agente por suite.

## 10 — Paralelizacion con worktrees

N/A — secuencial por dependencias (migration -> login -> overview -> front).

## Parte A — refactor de tests

- Ningun test referencia la operation `register` ni sus controllers/UI:
  - `rg -l "controllers/register|operation.*=.*register|registerStart|RegisterForm|use-register" serverless/lambda/services/auth admin/src admin/tests`
    -> cero.
- Ningun test asume `mfa.list` con solo 3 campos (ahora incluye `required`).
- Los tests nuevos estan en la ruta/convencion correcta (un archivo por
  escenario; mirror en `admin/tests/unit/`).
- `api_e2e` actualizado: el harness E2E ya NO usa `register.*` (usa `login`
  para crear+verificar). Revisar `devtools/api_e2e`.

## Parte B — bateria local (repo verde)

```bash
# Migration (en branch Neon de prueba primero)
neon branches create --name test-00000005 --parent main   # via neonctl
# apuntar DATABASE_URL al branch y correr upgrade/downgrade/upgrade
python devtools/run.py serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev
python devtools/run.py serverless run --stage=dev --lambda=db --event=events/current.json --aws-profile=tfs-dev

# Backend auth
python devtools/run.py serverless lint-deps --lambda=auth --shared
python devtools/run.py serverless tests --type=unit --lambda=auth
python devtools/run.py serverless tests --type=coverage --lambda=auth   # >=80%
python devtools/run.py serverless tests --type=unit --shared
python -m compileall -q serverless/lambda/services/auth/core

# Frontend admin
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin test          # coverage >=80% per-file
pnpm --filter @portfolio/admin build
```

Bucle: si algo falla -> corregir -> re-ejecutar. No declarar listo con rojo o
coverage <80%.

**Gate de cierre (push + PR)**: solo con Parte A+B verde. `git push` + PR ->
`dev`, esperar los 3 checks CI verdes, merge con `--merge`.

## Parte C — despliegue REAL (post-merge, OBLIGATORIA — toca infra + datos)

El merge a `dev` dispara `deploy-backend.yml` (migrate-db -> deploy-lambdas) y
`deploy-apps.yml` (admin). Tras esperar ambos runs (`gh run watch`):

1. **Migration aplicada en dev** [AC-B1]:
   ```bash
   python devtools/run.py serverless run --stage=dev --lambda=db \
     --event=events/current.json --aws-profile=tfs-dev   # revision 00000005
   ```

2. **`check-email` real** [AC-Z1]:
   ```bash
   # email nuevo -> exists:false ; email existente -> exists:true + methods
   curl -s -X POST https://api.portfolio.dev.the-full-stack.com/auth \
     -H 'content-type: application/json' \
     -d '{"operation":"login","action":"check-email","email":"<nuevo>@test","cf_turnstile_response":"<bypass>"}'
   ```
   (usar el token de bypass Ed25519 del harness api_e2e para dev).

3. **`login.start` crea + email** [AC-Z2]: disparar `login.start` con un email
   nuevo en dev; confirmar UN email con magic-link + code; click al link -> 302
   a admin/callback; code en `/login` paso verify -> login OK.

4. **`required` exige el metodo** [AC-Z3]: en una cuenta de dev con TOTP
   `required`, el login pide el TOTP; un recovery code lo saltea. Verificar via
   `api_e2e --env=dev` (extender el harness con el caso required).

5. **Panel real** [AC-Z4]: abrir `https://admin.portfolio.dev.the-full-stack.com`,
   login, ir a `/settings/security` (debe estar en el sidebar):
   - 1 sola consulta (`security.overview`) en la Network tab.
   - Los 5 metodos con su estado; toggle on/off y "requerido" persisten tras
     reload.
   - `curl -fsS -o /dev/null -w "HTTP %{http_code}\n"
     https://admin.portfolio.dev.the-full-stack.com/settings/security` -> 200.

Bucle de correccion identico a la Parte B. No declarar el plan "listo" sin la
Parte C verde (migration + check-email + login crea + required + panel real).

## 12 — Definition of Done

- [ ] AC-B*, AC-C*, AC-D*, AC-A*, AC-E*, AC-Z* con test que los cubre y pasa.
- [ ] Migration 00000005 aplicada en dev (upgrade+downgrade probados en branch).
- [ ] Coverage per-file >= 80% (auth + admin).
- [ ] `serverless lint-deps` + `pnpm typecheck/lint` limpios.
- [ ] Build estatico del admin OK; `/settings/security` en el sidebar.
- [ ] La operation `register` y su UI eliminadas (rg cero).
- [ ] `auth-system.md` actualizada y validada con `claude -p`.
- [ ] CI (3 checks) verde; PR mergeado a dev con `--merge`.
- [ ] Parte C verde (check-email + login crea + required + panel real en dev).
- [ ] Carpeta `docs/specs/admin-security-overview/` eliminada en el ultimo
      commit.

[<- commits](08-commits.md) | [README ->](README.md)
