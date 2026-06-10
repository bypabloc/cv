# 04 — Fase 1: backend — Lambda `cv_admin`

> Operations `content` (escritura CV) y `publish` (redeploy de apps).
> Patron lambda-controller + shared-only imports. [Volver al README](README.md).

## 1.1 Refactor previo: helpers de escritura a `shared.db`

Extraer de `services/db/core/services/seed_service.py` los helpers
genericos a un repositorio de escritura reutilizable:

- `serverless/lambda/shared/db/repositories/cv_write.py`:
  - `upsert_entity(session, model, natural_key, values) -> id`
  - `set_translation(session, entity_type, entity_id, field, locale, value)`
  - `link_niches(session, junction, entity_id, niche_slugs)` (reescribe)
  - `set_niche_priorities(session, entity_type, entity_id, priority_map)`
  - `ensure_skill(session, name) -> id` / `ensure_tech_tag(...)`
  - upserts compuestos por entidad: `upsert_experience(session, data)`,
    `upsert_project(...)`, `upsert_profile(...)`, `upsert_simple(...)`
    (certificates/awards/languages/endorsements/publications/education),
    `upsert_skill_category(...)`, y `delete_<entidad>(session, slug)`.
- `seed_service.py` pasa a consumir `cv_write` (cero duplicacion). El
  comportamiento del seed NO cambia (mismos upserts).
- Los deletes borran explicitamente hijos + uniones + i18n + priorities
  (no confiar en CASCADE para las polimorficas: `i18n_translations` y
  `tax_niche_priorities` no tienen FK a la entidad).

Tests: unit en `shared/tests/unit/shared/db/` por helper (asserts
exactos, BDD docstring). El guard de FKs existente debe seguir verde.

## 1.2 Lambda nuevo `cv_admin`

Scaffold lambda-controller en `serverless/lambda/services/cv_admin/`:

- `manifest.yaml`: runtime python3.13, `memory: 256` (importa shared.db;
  minimo de lambda-config — MEDIR tras deploy y ajustar comentario),
  `timeout: 30`, `snap_start: false`, trigger `http POST /cv-admin`.
  `uses`: tables `cache: read-write` (invalidacion por tag) + las tablas
  de rate-limit + `jwt-blacklist: read`; secrets `neon-url`, `jwt-secret`,
  `admin-emails`, `github-deploy-token`. CORS por env: SOLO los origins
  del admin (`admin.portfolio.{dev|prod}.the-full-stack.com`).
- `core/handler.py`: delgado, `http_handler(event, event_model=...,
  cors_origin='echo', metric_names={...})`.
- Auth transversal (patron `users`): `require_active_user` (access JWT +
  blacklist + status en Neon) + `require_admin` (whitelist SSM). No-admin
  → `404 NOT_FOUND`. Rate-limit `check_or_raise` con
  `turnstile_validated=False` + reglas seedeadas para `content.*` y
  `publish.*`.
- `core/models/content.py`: models Pydantic espejo del shape YAML del
  seed (BiLang `{es, en}`, `niches: list[str]`, `priority: dict[str,int]`,
  bullets `{es: [...], en: [...]}`, metrics, stack, caseStudy, etc.).
  Validaciones: slug kebab-case, niches ∈ catalogo, fechas `YYYY-MM` o
  `YYYY-MM-DD` segun entidad (mismas reglas del seed).
- `core/controllers/content/<action_snake>.py`: un controller por action
  (tabla del contrato en [02-arquitectura-flujos.md](02-arquitectura-flujos.md)).
  Orquestan: validar → service → normalizar.
- `core/services/content_service.py`: abre LA transaccion, llama a
  `shared.db.repositories.cv_write`, commit, e invalida cache:
  `invalidate_tag('cv')` (modulo `shared.cache`). Errores →
  `ServiceError` con codigo `4xxx` (ej. `SLUG_NOT_FOUND` en delete).
- `core/services/publish_service.py`: lee el PAT de SSM
  (`get_secret_by_name('github-deploy-token')`), `POST` a
  `https://api.github.com/repos/bypabloc/cv/actions/workflows/
  deploy-apps.yml/dispatches` con `{ref, inputs:{env}}` (httpx via el
  portador shared que corresponda — si no existe portador HTTP client,
  agregarlo segun el procedimiento de lambda-shared-imports). `status`
  consulta el ultimo run del workflow para el ref. NUNCA loguear el PAT.
- `pyproject.toml` PEP 621 sin deps que ya aporte el cierre de shared
  (`lint-deps` verde).

## 1.3 Reglas de la escritura compuesta

- Upsert de experience: upsert entidad → reemplazar bullets por kind
  (delete + insert ordenado; la PK (experience_id, kind, position) hace
  fragil el update in-place) → sync skills (ensure + reemplazo de
  uniones) → i18n (`role`) → niches → priorities. TODO en una tx.
- Upsert de project: idem con case study (1:1), metrics (reemplazo
  ordenado), stack (ensure tech tags + uniones con position).
- `reorder`: valida que `ordered_slugs` sean exactamente las entidades
  del niche; asigna prioridades descendentes (paso 10) y reescribe.
- Profile: singleton — upsert por `handle`; stats 1:1.

## 1.4 Seeds de rate-limit

Agregar reglas para los endpoints nuevos (patron de
`.claude/docs/auth-system/03-rate-limit-rules.md`): `content.*` ~30/min
por IP, `publish.dispatch` ~3/min (es un trigger de CI).

## Tests requeridos (seccion 6 de esta fase)

- 6.A TDD: `WHEN upsert-experience con slug nuevo THEN crea entidad +
  bullets + uniones [AC-1]`; `WHEN delete-project THEN borra hijos +
  i18n + priorities [AC-4]`; `WHEN reorder THEN prioridades descendentes
  [AC-5]`; `WHEN user no-admin THEN 404 [AC-2]`.
- 6.B Unit (pytest, un archivo por escenario): models + services +
  controllers + handler por action. Mock de E/S externa (Neon session,
  GitHub API, SSM); NUNCA mockear services propios.
- Coverage >= 80% per-file:
  `serverless tests --type=coverage --lambda=cv_admin`.
- `serverless lint-deps --lambda=cv_admin` y `--shared` exit 0.
- Integration/E2E del Lambda desplegado: NO se duplica una suite
  `tests/integration/` propia — la cubre la capa api del harness `e2e`
  con los specs detallados de [11-specs-e2e-api.md](11-specs-e2e-api.md)
  (lifecycle completo por entidad contra dev).

## Archivos afectados (Fase 1)

### Crear

- `serverless/lambda/shared/db/repositories/cv_write.py` — helpers escritura
  - Verificar: `serverless tests --type=unit --shared`
- `serverless/lambda/services/cv_admin/**` — manifest, core (handler,
  models, controllers content+publish, services, settings), pyproject,
  events de ejemplo, tests
  - Verificar: `serverless tests --type=unit --lambda=cv_admin` +
    `lint-deps --lambda=cv_admin`

### Modificar

- `serverless/lambda/services/db/core/services/seed_service.py` — consumir
  `cv_write` (sin cambio de comportamiento)
  - Verificar: `serverless tests --type=unit --lambda=db`
- Seeds de rate-limit (donde viven las reglas actuales) — reglas
  `content.*` / `publish.*`
  - Verificar: test unit de las reglas nuevas

### Deploy (dev)

```bash
python devtools/run.py serverless deploy --lambda=cv_admin --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless status --lambda=cv_admin --stage=dev --aws-profile=tfs-dev
# Medir memoria minima real (procedimiento de lambda-config.md) y ajustar manifest
```
