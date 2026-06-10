# 11 — Specs E2E capa API (`tests/api/`) — detalle completo

> Un archivo = un escenario. Docstring BDD + cuerpo AAA + asserts EXACTOS.
> Corren contra dev desplegado (`e2e --module=api --env=dev`). NUNCA prod.
> [Volver al README](README.md).

## Fixtures compartidas (en `tests/api/_flows.py` + conftest del modulo)

- `cv_admin_session` (session-scoped): crea user sintetico activo
  (`e2e-cvadm-<rand>@simulator.amazonses.com`) via flujo login con seed de
  code en Neon (`tests/shared/environment`), lo promueve a la whitelist
  SSM `admin-emails` con `_wait_ssm_promoted` ANTES del bust de cache
  (gotcha conocido del modulo `admin.*`), y obtiene el access JWT.
  Teardown: restaurar whitelist original + borrar el user + sus datos.
- `cv_admin_post(action, data, *, operation='content')`: helper httpx
  `POST /cv-admin` con `Authorization: Bearer` + timing via el Runner del
  modulo (reporter de tiempos como el resto de `tests/api`).
- `cv_get(action, niche=None, locale=None)`: GET /cv publico sin auth.
- `synthetic_slug(prefix)`: `e2e-cvadm-<prefix>-<rand6>`. TODO lo creado
  usa este prefijo; el conftest del modulo registra los slugs creados y el
  teardown ejecuta `delete-<entidad>` idempotente por cada uno (y
  verifica con GET que no quedan).
- Regla dura: los lifecycles crean SOLO entidades sinteticas. Las dos
  excepciones (profile singleton y reorder, que tocan datos reales de dev)
  tienen snapshot + restore obligatorio especificado abajo.

## Plantilla canonica "full lifecycle" (aplica a cada entidad)

Cada `test_cv_admin_<entidad>_full_lifecycle.py` ejecuta ESTOS pasos, con
el payload completo de su tabla (ningun campo opcional sin cubrir):

1. **CREATE**: `upsert-<entidad>` con payload completo → assert
   `status == 200`, `is_valid is True`, `code == 0`, y el `data` devuelto
   contiene la entidad normalizada (asserts campo a campo, incluidos los
   BiLang `{es, en}` y los hijos en el orden enviado).
2. **READ publica + cache**: `cv_get('<seccion>')` → la entidad sintetica
   aparece (la invalidacion por tag `cv` ya corrio). Asserts EXACTOS de
   cada campo: textos es y en, fechas, urls, hijos en orden, niches.
3. **READ por niche**: `cv_get('<seccion>', niche=<n1>)` la incluye;
   `cv_get('<seccion>', niche=<n2-no-asignado>)` NO la incluye.
4. **UPDATE**: re-upsert con mutaciones especificas (tabla por entidad:
   minimo un texto es, un texto en, un hijo agregado al INICIO, un hijo
   eliminado, un cambio de niches) → GET refleja: orden de hijos exacto
   post-mutacion, elemento eliminado ausente, niche nuevo filtra bien.
5. **DELETE**: `delete-<entidad> {slug}` → `code == 0`; GET ya no la
   lista en NINGUN niche; los textos i18n no aparecen en otras entidades
   (sin huerfanos visibles).
6. **DELETE idempotencia**: segundo delete del mismo slug → error de
   negocio EXACTO (`is_valid is False`, `code == 4404` SLUG_NOT_FOUND —
   ajustar al codigo definitivo de la Fase 1, asserts `==`).

## Payloads completos por entidad (paso 1 y mutaciones del paso 4)

| Spec | Payload CREATE (todos los campos) | Mutaciones UPDATE |
|------|-----------------------------------|-------------------|
| `test_cv_admin_experience_full_lifecycle.py` | slug, role{es,en}, company, country, companyUrl, start `YYYY-MM`, end `YYYY-MM`, seniority `senior`, metricsEstimated true, responsibilities{es:[2],en:[2]}, achievements{es:[2],en:[2]}, skillsTechnical [2 del catalogo + 1 NUEVA], skillsSoft [1], niches [generic, vibe], priority {generic: 5, vibe: 3} | role.en; responsibility nueva en posicion 0; achievement[1] eliminado; skillsTechnical sin la nueva; niches → solo [generic]; end → null (Presente) |
| `test_cv_admin_project_full_lifecycle.py` | slug, name, url, repo, links [2 {label,url}], status `active`, projectType `web`, isConfidential false, metricsEstimated true, description{es,en}, metrics [2 {key,value} ordenadas], stack [2 tags existentes + 1 NUEVO], caseStudy {problem,process,result}{es,en}, niches [generic], priority {generic: 4} | metric nueva al inicio; metric[1] eliminada; stack sin el nuevo tag; caseStudy.result.en; status → `inactive` |
| `test_cv_admin_education_full_lifecycle.py` | slug, institution, degree{es,en}, description{es,en}, start, end, url, niches [generic] | degree.es; end → null; url |
| `test_cv_admin_certificate_full_lifecycle.py` | slug, title, issuer, date, url, niches [generic, fintech] | title; niches → [generic] |
| `test_cv_admin_award_full_lifecycle.py` | slug, issuer, date, url, title{es,en}, motivation{es,en}, niches [generic] | motivation.en; url → null |
| `test_cv_admin_language_full_lifecycle.py` | slug, name{es,en}, level{es,en}, niches [generic] | level.es |
| `test_cv_admin_endorsement_full_lifecycle.py` | slug, name, role, company, linkedin, relation{es,en}, niches [generic] | relation.en; company → null |
| `test_cv_admin_publication_full_lifecycle.py` | slug, title, platform, url, canonicalUrl, date, niches [generic] | canonicalUrl → null; title |
| `test_cv_admin_skill_category_full_lifecycle.py` | slug, kind `technical`, name{es,en}, skills [3 ordenadas, 1 NUEVA], niches [generic] | skill movida de posicion 2→0; una skill eliminada; name.en |

## Specs unicos (fuera de la plantilla)

### `test_cv_admin_profile_full_lifecycle.py` (singleton — snapshot/restore)

1. SNAPSHOT: `cv_get('profile')` → guardar la respuesta COMPLETA original.
2. UPSERT: `upsert-profile` cambiando headline{es,en}, summary{es,en},
   availability{es,en}, location, stats (years/companies/countries/
   certifications) con valores marcador `E2E-CVADM-<rand>`.
3. VERIFY: GET refleja cada marcador (asserts exactos por campo).
4. RESTORE: `upsert-profile` con el snapshot original COMPLETO.
5. VERIFY RESTORE: GET == snapshot original campo a campo (el CV real de
   dev queda intacto). El restore corre tambien en teardown `finally`.

### `test_cv_admin_reorder_full_lifecycle.py` (toca orden real — restore)

1. ARRANGE: crear 3 experiencias sinteticas en niche `generic`
   (priorities 1, 2, 3).
2. SNAPSHOT: GET `experiences?niche=generic` → guardar el orden COMPLETO
   actual (slugs reales + sinteticos).
3. REORDER: `reorder {entity_type:'experience', niche:'generic',
   ordered_slugs:[...]}` con la lista completa, moviendo SOLO las 3
   sinteticas al final en orden invertido (las reales conservan posicion
   relativa).
4. VERIFY: GET → posiciones relativas exactas: reales sin cambio entre
   si; sinteticas al final en el orden enviado.
5. RESTORE: `reorder` con el orden del snapshot → GET == snapshot.
6. CLEANUP: delete de las 3 sinteticas; GET == estado pre-test.
7. Edge: `reorder` con `ordered_slugs` incompleto (falta un slug del
   niche) → error de validacion exacto (`code == 1xxx` definitivo).

### `test_cv_admin_catalogs.py`

- `catalogs {}` → `niches` == lista exacta de 5 slugs en `display_order`
  (`['fintech','architect','leader','vibe','generic']` — confirmar orden
  canonico en Fase 1); `skills` y `techTags` son listas de `{slug,name}`
  que contienen entradas conocidas del CV real (asserts de presencia con
  `in` + shape exacto de un elemento).

### `test_cv_admin_auth_missing_jwt.py`

- POST sin `Authorization` a `content.upsert-experience` Y a
  `publish.dispatch` → `status == 401` exacto en ambas, body de error del
  contrato (sin filtrar detalles).

### `test_cv_admin_auth_non_admin_404.py`

- User sintetico activo NO promovido a whitelist → access JWT valido →
  `content.upsert-experience`, `content.catalogs` y `publish.dispatch` →
  `status == 404` con `error == 'NOT_FOUND'` exacto (anti-enumeracion:
  mismo body que una ruta inexistente). [AC-2]

### `test_cv_admin_validation_errors.py`

Con sesion admin, una sub-aserción por caso (mismo escenario):

1. slug con mayusculas/espacios → `1xxx` exacto, nada persiste (GET).
2. niche inexistente `no-such-niche` → error exacto; nada persiste.
3. fecha malformada (`2026-13`) → `1xxx`; nada persiste.
4. action desconocida `upsert-nope` → error de operation/action (4xx).
5. payload sin `slug` → `1xxx` con el campo señalado.

### `test_cv_admin_cache_invalidation.py`

1. GET `experiences` (puebla cache) → guardar respuesta.
2. `upsert-experience` sintetica → GET inmediato la incluye (la
   invalidacion por tag funciono — sin esperar TTL 900s). [AC-3]
3. `delete` → GET inmediato ya no la incluye.

### `test_cv_admin_publish_dispatch_full_lifecycle.py` (marker `publish`)

> Dispatch REAL en dev (encola un run de deploy-apps; aceptable, con
> `concurrency` queue). Marker pytest `publish` para excluirlo de
> corridas frecuentes: `-m "not publish"`.

1. `t0` = now UTC.
2. `publish.dispatch {}` → `code == 0`.
3. Poll `publish.status` (backoff, max 60s) hasta ver un run del workflow
   `deploy-apps.yml` con `ref == 'dev'` y `created_at > t0`.
4. Assert shape exacto del status: `{status, url, created_at}` con
   `status in {'queued','in_progress','completed'}` (enum exacto) y `url`
   apuntando a `github.com/bypabloc/cv/actions/runs/`.
5. NO espera el deploy completo (lo verifica la Parte C del plan).

### `test_cv_admin_publish_status.py`

- `publish.status {}` sin dispatch previo en el test → devuelve el ultimo
  run real del ref `dev` con el shape exacto (campos y tipos).

### `test_cv_admin_rate_limit_content.py` (marker `slow`)

- Con IP fija dedicada (fuera del pool del `IpRotator`) y buckets
  limpios: `catalogs` consecutivos hasta el primer `429` (cap 2x limite).
  Invariantes: nunca un `429` antes de 30 doscientos, y el body/headers
  del `429` EXACTOS (`RATE_LIMIT_EXCEEDED` + extra + `Retry-After`). El
  conteo de 200s no es exacto: el sliding window weighted bucketiza por
  el reloj del Lambda y el drift puede partir la rafaga en 2 ventanas.

## Cobertura AC de esta capa

| AC | Specs |
|----|-------|
| AC-1, AC-3, AC-4 | lifecycles + cache_invalidation |
| AC-2 | auth_non_admin_404, auth_missing_jwt |
| AC-5 | reorder_full_lifecycle |
| AC-7 | publish_dispatch, publish_status |
| AC-11 | cada lifecycle (GET publico sin auth en pasos 2-3) |
| AC-12 | implicito: todo corre contra el branch Neon de dev (Fase 0) |
