# 01 — Contexto, solucion y criterios de aceptacion

> Secciones 1-3 del plan. [Volver al README](README.md).

## 1. Contexto / Problema

Hoy el CV solo se edita tocando YAML en
`serverless/lambda/services/db/core/seeds/data/` y corriendo el seed de la
Lambda `db` (idempotente, `INSERT ... ON CONFLICT DO UPDATE`). No hay
ninguna via de escritura HTTP: el Lambda `cv` es read-only (GET /cv, 10
actions, `@cached(ttl=900, stale=86400, tags=['cv'])`). El usuario quiere
editar su curriculum de forma interactiva desde el panel admin.

### Hallazgos de exploracion

- Schema: ~30 tablas `cv_*` + `i18n_translations` (polimorfica, PK
  entity_type+entity_id+field+locale) + `tax_niche_priorities` (orden por
  niche) + catalogos `tax_niches` / `tax_tech_tags` / `cv_skills`. Clave
  natural: `slug` en toda entidad (profile usa `handle`).
- El sitio publico es ESTATICO: cada build de las apps corre
  `packages/content/scripts/fetch-cv-cache.mjs` (prebuild) que fetchea
  GET /cv y materializa JSON en `packages/content/src/data-cache/`.
  Editar la DB NO cambia el sitio publicado hasta un redeploy de apps.
- `seed_service.py` ya tiene la logica de upsert transversal
  (`_upsert_returning_id`, `_set_translation`, `_link_niches`,
  `_set_niche_priorities`) — reutilizable para la API de escritura.
- El admin ya tiene la ruta `/cv` (placeholder "plan futuro
  c-cv-management"), nav item, `api-client` con mutex refresh y el patron
  feature (api/hooks/components/validation + MSW).
- `deploy-apps.yml` ya soporta `workflow_dispatch` con `inputs.env`.
- `shared/auth/admin.py` ya implementa `require_admin` (whitelist SSM).
- Riesgo conocido: `/portfolio/dev/neon-url` se creo copiando el valor
  legacy que apunta al branch `production` de Neon — escribir desde el
  admin de dev podria mutar datos de prod (Fase 0 lo resuelve).

## 2. Solucion Propuesta

La DB Neon pasa a ser la fuente de verdad del CV. Se agrega un Lambda
nuevo **`cv_admin`** (lambda-controller, `POST /cv-admin`, auth admin) con
dos operations:

- `content`: upsert/delete/reorder por entidad (espejo del shape YAML del
  seed, validado con Pydantic), transaccional, con invalidacion del cache
  tag `cv` al commit.
- `publish`: dispara `workflow_dispatch` de `deploy-apps.yml` del env via
  GitHub API (PAT fine-grained en SSM) y expone el estado del ultimo run.

El admin agrega la feature `cv-management`: sub-rutas por seccion del CV
(espejando el sitio publico), forms shadcn con es/en lado a lado,
asignacion de niches, reorden por prioridad (por niche) y boton "Publicar
cambios".

El seed YAML del repo se ELIMINA. Lo reemplaza:

- `devtools db_export`: exporta la DB a YAML seed-compatible y lo sube a
  S3 (`portfolio-db-backups`, versioning + lifecycle 12 semanas).
- Workflow `db-backup.yml`: cron semanal + dispatch manual, dev y prod,
  rol OIDC dedicado.
- El command `seed` de la Lambda `db` pasa a leer los YAML desde S3
  (restore) con guard `confirm_overwrite`.

### Decisiones clave

- **Decision 1: Lambda nuevo `cv_admin`, no extender `cv`** — el trigger
  del manifest es de un solo metodo (GET); extenderlo implica tocar el
  provisioner. Un Lambda nuevo separa superficie publica de admin, con
  IAM scoped (patron `users`). Memoria inicial 256 MB (importa
  `shared.db`; minimo de la regla lambda-config), MEDIR tras deploy.
- **Decision 2: contrato de payload = shape YAML del seed** — los models
  Pydantic del `cv_admin` espejan el YAML actual (`slug`, `role: {es,en}`,
  `niches`, `priority: {niche: n}`, ...). Minimiza traduccion mental,
  reusa los helpers del seed y hace el export/restore simetrico.
- **Decision 3: el admin LEE del GET /cv publico existente** (sin filtro
  niche, BiLang ya incluido) — la invalidacion por tag tras cada escritura
  garantiza lecturas frescas. No se duplica un read-path admin.
- **Decision 4: publicar es explicito** — el guardado solo toca la DB; el
  boton "Publicar" del admin dispara el redeploy. Sin auto-deploy.
- **Decision 5: catalogo on-the-fly** — skills y tech-tags se upsertean
  al guardar la entidad que los referencia (como hace el seed), ademas de
  una action `catalogs` para poblar selects del admin.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given un admin autenticado (access JWT + whitelist SSM), When
  envia `POST /cv-admin {operation:'content', action:'upsert-experience',
  data:{slug, ...}}`, Then la experiencia se upserta por slug con bullets,
  skills, niches, priorities e i18n en UNA transaccion y responde el
  registro normalizado con `is_valid: true`.
- **AC-2**: Given un user con JWT valido pero NO admin, When llama
  cualquier action de `cv_admin`, Then recibe `404 NOT_FOUND`
  (anti-enumeracion).
- **AC-3**: Given una escritura exitosa, When se consulta GET /cv, Then la
  respuesta refleja el cambio (cache tag `cv` invalidado en el commit).
- **AC-4**: Given `delete-<entidad>` con un slug existente, When se
  ejecuta, Then se eliminan la entidad, sus hijos, uniones niches,
  priorities e i18n, y GET /cv deja de listarla.
- **AC-5**: Given el admin en una seccion con selector de niche, When
  reordena entradas, Then `tax_niche_priorities` se actualiza para ese
  niche y el orden persiste al recargar.
- **AC-6**: Given el form de una entidad, When el admin edita campos es/en
  y guarda, Then ve toast de exito y la lista refleja el cambio sin
  recargar la pagina (invalidate de Tanstack Query).
- **AC-7**: Given el boton "Publicar cambios", When el admin confirma,
  Then `cv_admin` dispara `workflow_dispatch` de `deploy-apps.yml` con el
  ref del env y la UI muestra confirmacion + link a los runs.
- **AC-8**: Given el workflow `db-backup.yml` (cron semanal o dispatch),
  When corre, Then sube a S3 un snapshot YAML seed-compatible por entidad
  para dev Y prod bajo paths fechados (`<stage>/<YYYY-MM-DD>/...` +
  `<stage>/latest/...`).
- **AC-9**: Given tablas cv con datos, When se invoca el command `seed`
  sin `confirm_overwrite: true`, Then aborta con error explicito; con el
  flag y un `source` S3, restaura ese snapshot.
- **AC-10**: Given el repo tras la Fase 2, When se busca
  `services/db/core/seeds/data/`, Then no existe; el seed resuelve su
  fuente desde S3.
- **AC-11**: Given un visitante publico, When hace GET /cv, Then el
  comportamiento actual no cambia (read-only, cache, CORS, sin auth).
- **AC-12**: Given el entorno dev tras la Fase 0, When se escribe via
  `cv_admin` en dev, Then los cambios ocurren en el branch Neon de dev y
  prod NO se ve afectado.
- **AC-13**: Given un user autenticado NO admin, When abre el admin, Then
  el sidebar NO muestra "Gestion CV" y el acceso directo a `/cv` (o una
  sub-ruta) muestra la pantalla de no autorizado (mismo tratamiento 404
  anti-enumeracion que `users-admin`), sin redirect a login ni crash.
