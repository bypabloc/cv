# 10 — Secciones 11-12: verificacion E2E iterativa y Definition of Done

> Ultima fase y ultimo commit. Bucle: ejecutar → diagnosticar → corregir
> → re-ejecutar. NO se cierra con un comando en rojo.
> [Volver al README](README.md).

## Parte A — refactor de tests

- Ningun test referencia `seeds/data/` ni el flujo de seed local
  eliminado: `rg -l "seeds/data" tests serverless devtools` → solo
  referencias historicas en changelogs (ideal: cero).
- Tests nuevos en su ruta y convencion: un archivo por escenario,
  docstring BDD, asserts exactos (api: `tests/api/test_cv_admin_*.py`;
  admin: `tests/admin/test_cv_*.py`; unit backend en el lambda y shared;
  unit admin en `admin/tests/unit/features/cv-management/`).
- MSW handlers del admin reflejan el contrato REAL (flat body + Envelope).

## Parte B — bateria de comandos reales

```bash
# Backend
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=unit --lambda=cv_admin
python devtools/run.py serverless tests --type=coverage --lambda=cv_admin   # >=80%
python devtools/run.py serverless tests --type=unit --lambda=db
python devtools/run.py serverless lint-deps

# Devtools
python devtools/run.py test_runner --module=devtools --type=unit

# Admin
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin test:coverage     # >=80% per-file
pnpm --filter @portfolio/admin build

# Monorepo (gate pre-push)
pnpm run lint && pnpm run typecheck && pnpm run test && pnpm run build

# Deploy dev + E2E contra dev desplegado
python devtools/run.py serverless deploy --lambda=cv_admin --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=db --stage=dev --aws-profile=tfs-dev
python devtools/run.py e2e --module=api --env=dev --aws-profile=tfs-dev
python devtools/run.py e2e --module=admin --env=dev --aws-profile=tfs-dev
```

Los E2E NO son smoke superficial: cubren el flujo completo de CADA
interfaz, de principio a fin, segun los dos catalogos de specs (cada spec
con sus pasos numerados, payloads completos y asserts exactos):

- [11-specs-e2e-api.md](11-specs-e2e-api.md) — ~19 specs: lifecycle
  completo por entidad (create → GET publica → filtro por niche → update
  con mutaciones → delete → idempotencia), profile y reorder con
  snapshot/restore, catalogs, cache invalidation, auth (401/404),
  validacion, publish dispatch real (marker `publish`) + status, y
  rate-limit (marker `slow`).
- [12-specs-e2e-admin.md](12-specs-e2e-admin.md) — ~14 specs browser:
  navegacion por las 10 sub-rutas con conteos contra el API, flujo
  create→hidratacion exacta→edit→delete por CADA seccion (todos los
  campos es/en llenados y verificados), reorden con restore, publish UI
  (interceptado; el dispatch real es de la capa API), validacion de
  forms, y AC-13 (no-admin no ve `/cv`).

```bash
# corrida completa (incluye dispatch real de publish):
python devtools/run.py e2e --module=api --env=dev --aws-profile=tfs-dev
# corrida frecuente sin disparar deploys ni rate-limit:
#   pytest markers: -m "not publish and not slow"
python devtools/run.py e2e --module=admin --env=dev --aws-profile=tfs-dev
```

Criterio de completitud de la Parte B: TODOS los specs de los docs 11 y
12 existen, pasan, y ningun AC queda sin al menos un spec que lo cubra
(matrices de cobertura al final de cada doc).

Gate: `git push` + PR `feature/c-cv-management -> dev` SOLO con A+B verdes.

## Parte C — verificacion de despliegue REAL (post-merge)

1. Merge a `dev` dispara `deploy-backend.yml` + `deploy-apps.yml`: revisar
   `conclusion` global Y de CADA job (`gh run view <id> --json jobs`).
2. Curl real:
   - `POST https://api.portfolio.dev.the-full-stack.com/cv-admin` sin
     auth → 401/404 (nunca 5xx).
   - `GET https://api.portfolio.dev.the-full-stack.com/cv?operation=cv&action=profile`
     → 200 con el profile.
   - `https://admin.portfolio.dev.the-full-stack.com/cv/` → 200.
3. Flujo real en dev: editar un campo desde el admin → Publicar →
   esperar el run de deploy-apps → curl al sitio dev y verificar el
   marcador editado en el HTML.
4. Backup real: dispatch manual de `db-backup.yml` → objetos en
   `s3://portfolio-db-backups/{dev,prod}/latest/`.
5. Promocion a prod (PR `dev -> main`) repite 1-3 contra prod (el publish
   de prod usa ref `main`).

## 12. Validacion y Definition of Done

Pre-implementacion:

- [ ] AC numerados y referenciados por tests
- [ ] Fase 0 completada (Neon dev aislado — AC-12) ANTES de exponer escritura
- [ ] Tests TDD del backend escritos y fallando (Red)
- [ ] `pnpm install` limpio; dev server admin arranca

Definition of Done:

- [ ] Todos los AC (1-12) cubiertos por al menos un test que pasa
- [ ] Coverage >= 80% per-file en archivos modificados (backend, devtools, admin)
- [ ] Typecheck + Biome + Ruff sin errores; `lint-deps` exit 0
- [ ] Build estatico del admin y de las 6 apps exitoso
- [ ] E2E api + admin verdes contra dev
- [ ] Parte C verde (HTTP reales como evidencia)
- [ ] Docs/rules actualizadas (neon-management, serverless-backend, admin)
- [ ] `git rm -r docs/specs/c-cv-management/` en el ultimo commit
