# 02 — Arquitectura y flujos de datos

> Secciones 4-5 del plan. [Volver al README](README.md).

## 4. Diagrama de Flujo (Antes y Despues)

### Antes

```text
dev edita YAML (seeds/data/) --git push--> repo
        |
        v
serverless run --lambda=db --event=seed.json   (manual)
        |
        v
   Neon (cv_*)  <--read--  Lambda cv (GET /cv, cache DDB tag 'cv')
        |                        ^
        |                        | prebuild fetch-cv-cache.mjs
        v                        |
   (sin escritura HTTP)    build apps Astro --> Cloudflare Pages
```

### Despues

```text
admin /cv (Next SPA) --POST /cv-admin {content.*}--> Lambda cv_admin
        |                     |  require_active_user + require_admin
        |                     v
        |              tx: entidad + hijos + i18n + niches + priorities
        |                     |
        |                     +--> invalidate cache tag 'cv'
        |                     v
        |                  Neon (cv_*)  <--read--  Lambda cv (GET /cv)
        |                                               ^
        +--POST {publish.dispatch}--> GitHub API        | prebuild fetch
                    |                                   |
                    v                                   |
        workflow_dispatch deploy-apps.yml --> build --> Cloudflare Pages

backup semanal (cron GH Actions):
  devtools db_export --stage=dev|prod --> YAML seed-compatible --> S3
restore:
  seed (Lambda db) --source=s3://...  --confirm_overwrite--> Neon
```

## 5. Diagrama ER

N/A — no hay cambios de schema: la escritura usa las tablas existentes
(`cv_*`, `i18n_translations`, `tax_niche_priorities`, `tax_niches`,
`tax_tech_tags`, `cv_skills`). No se agregan columnas ni tablas.

## Contrato de la API `cv_admin` (resumen)

`POST /cv-admin`, body `{operation, action, data}`, header
`Authorization: Bearer <access JWT>`.

### Operation `content`

| Action | data (clave) | Efecto |
|--------|--------------|--------|
| `upsert-profile` | shape del profile del seed (incl. stats, headline/summary i18n, niches) | upsert singleton |
| `upsert-experience` / `delete-experience` | shape YAML experience / `{slug}` | upsert/delete completo (bullets, skills, niches, priority) |
| `upsert-project` / `delete-project` | shape YAML project / `{slug}` | upsert/delete completo (case study, metrics, stack, niches, priority) |
| `upsert-education` / `delete-education` | shape YAML / `{slug}` | idem |
| `upsert-certificate` / `delete-certificate` | shape YAML / `{slug}` | idem |
| `upsert-award` / `delete-award` | shape YAML / `{slug}` | idem |
| `upsert-language` / `delete-language` | shape YAML / `{slug}` | idem |
| `upsert-endorsement` / `delete-endorsement` | shape YAML / `{slug}` | idem |
| `upsert-publication` / `delete-publication` | shape YAML / `{slug}` | idem |
| `upsert-skill-category` / `delete-skill-category` | shape YAML / `{slug}` | idem (orden de skills incluido) |
| `reorder` | `{entity_type, niche, ordered_slugs: [...]}` | reescribe `tax_niche_priorities` del niche (prioridad descendente segun orden) |
| `catalogs` | `{}` | devuelve niches, skills y tech-tags para selects |

### Operation `publish`

| Action | data | Efecto |
|--------|------|--------|
| `dispatch` | `{}` | `POST /repos/bypabloc/cv/actions/workflows/deploy-apps.yml/dispatches` con `ref` segun stage (dev→`dev`, prod→`main`) e `inputs.env` |
| `status` | `{}` | ultimo run del workflow para el ref (estado + url) |

Errores: rangos del contrato lambda-controller (`1xxx` validacion, `4xxx`
negocio — ej. slug inexistente en delete —, `5xxx` GitHub API).
