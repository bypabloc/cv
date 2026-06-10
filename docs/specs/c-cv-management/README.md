# Plan: c-cv-management — edicion interactiva del CV desde el admin

> La DB Neon pasa a ser la fuente de verdad del CV. Un Lambda nuevo
> `cv_admin` (POST /cv-admin, solo admin) permite editar las ~11 secciones
> del CV desde el panel admin (`/cv`), con i18n es/en, niches y reorden por
> prioridad. Un boton "Publicar" dispara el redeploy de las 6 apps. El seed
> YAML del repo se elimina; un export semanal DB→YAML seed-compatible a S3
> lo reemplaza como backup/restore.

## Escala

**Large** (30+ archivos: backend + devtools + CI + admin UI + E2E).

## Cuando leer

| Archivo | Cuando leer |
|---------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Secciones 1-3: contexto, solucion, AC numerados |
| [02-arquitectura-flujos.md](02-arquitectura-flujos.md) | Seccion 4: flujo de datos antes/despues. Seccion 5: N/A |
| [03-fase-0-prerrequisitos.md](03-fase-0-prerrequisitos.md) | Aislamiento Neon dev, PAT GitHub, bucket S3, rol OIDC backup |
| [04-fase-1-backend-cv-admin.md](04-fase-1-backend-cv-admin.md) | Lambda `cv_admin`: operations content + publish |
| [05-fase-2-export-backup-seed.md](05-fase-2-export-backup-seed.md) | devtools `db_export`, cron semanal, seed desde S3, eliminar seeds/data |
| [06-fase-3-admin-ui.md](06-fase-3-admin-ui.md) | Feature `cv-management` del admin (rutas, forms, reorden, Publicar) |
| [07-descomposicion.md](07-descomposicion.md) | Seccion 8: tareas atomicas y paralelizables |
| [08-commits.md](08-commits.md) | Seccion 9: commits incrementales |
| [09-paralelizacion-worktrees.md](09-paralelizacion-worktrees.md) | Seccion 10: base secuencial + fases worktree-safe |
| [10-verificacion-e2e.md](10-verificacion-e2e.md) | Secciones 11-12: bateria E2E iterativa + DoD |
| [11-specs-e2e-api.md](11-specs-e2e-api.md) | Catalogo COMPLETO de specs E2E capa API (~19): lifecycle por entidad, auth, reorder, publish, cache |
| [12-specs-e2e-admin.md](12-specs-e2e-admin.md) | Catalogo COMPLETO de specs E2E browser (~14): flujo create→edit→delete por seccion, navegacion, publish UI, no-admin |

## Decisiones no-reabribles (confirmadas con el usuario, 2026-06-09)

| # | Decision | Eleccion |
|---|----------|----------|
| D-1 | Publicacion de cambios al sitio | Boton "Publicar" en el admin → `workflow_dispatch` de `deploy-apps.yml` |
| D-2 | Alcance fase 1 | TODO el CV (las ~11 secciones), plan multi-fase |
| D-3 | Destino del seed YAML | Eliminar `seeds/data/` del repo; script devtools de export DB→YAML + cron semanal |
| D-4 | Destino del backup | S3 con versioning + lifecycle (12 semanas) |
| D-5 | Formato del backup | YAML seed-compatible (restore = re-seed desde el snapshot) |
| D-6 | Envs respaldados | dev Y prod |
| D-7 | UX de edicion | Forms por seccion espejando el sitio + es/en lado a lado + niches + reorden |
| D-8 | Donde vive la API de escritura | Lambda NUEVO `cv_admin` (POST /cv-admin). El `cv` publico GET queda intacto (su trigger es de un solo metodo; extenderlo tocaria el provisioner) |

## Reglas criticas

- SIEMPRE las escrituras son transaccionales: entidad + hijos + i18n +
  niches + priorities en una sola tx; al commit, invalidar cache tag `cv`.
- SIEMPRE `require_active_user` + `require_admin` (whitelist SSM); no-admin
  recibe `404 NOT_FOUND` (anti-enumeracion, patron `users`).
- NUNCA tocar el comportamiento del Lambda `cv` publico (GET, cache, CORS).
- NUNCA habilitar escritura en dev sin completar la Fase 0 (aislamiento del
  branch Neon de dev) — hoy `/portfolio/dev/neon-url` puede apuntar a prod.
- SIEMPRE el seed (restore) exige `confirm_overwrite: true` sobre tablas
  con datos.
- Esta carpeta es efimera: se elimina con `git rm -r` en el ultimo commit.

## Estado por fase

| Fase | Estado |
|------|--------|
| 0 — Prerrequisitos infra | pendiente |
| 1 — Backend `cv_admin` | pendiente |
| 2 — Export/backup + seed S3 | pendiente |
| 3 — Admin UI `cv-management` | pendiente |
| 4 — Verificacion E2E + cierre | pendiente |
