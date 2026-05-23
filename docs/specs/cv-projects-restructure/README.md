# cv-projects-restructure

> Refactor del catalogo de proyectos del CV + agregar summary a experiences +
> mover casos de estudio al detalle de cada proyecto + dropdown de niches en
> nav + arreglo del hero del hub + fix del 403 en `/track`. Rama
> `feature/cv-projects-restructure` desde `dev`.

## Indice

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Contexto, solucion, AC | esta misma seccion mas abajo | Antes de implementar |
| Cambios de schema y data | [01-data-changes.md](01-data-changes.md) | Fases 1-3 |
| UI de proyectos + casos de estudio | [02-ui-changes.md](02-ui-changes.md) | Fase 4 |
| Nav dropdown + hub hero | [03-nav-and-hub.md](03-nav-and-hub.md) | Fases 5-6 |
| Summary en experiences | [04-experiences.md](04-experiences.md) | Fase 7 |
| Fix del /track 403 | [05-track-fix.md](05-track-fix.md) | Fase 8 |
| Secuencia de commits | [06-commits.md](06-commits.md) | Implementacion |
| Paralelizacion con worktrees | [07-paralelizacion.md](07-paralelizacion.md) | Implementacion |
| Verificacion E2E final | [08-verificacion-e2e.md](08-verificacion-e2e.md) | Cierre |

## Reglas criticas del plan

- Rama `feature/cv-projects-restructure`. NUNCA commitear en `dev`.
- Fuente unica de la data: `serverless/lambda/services/db/core/seeds/data/`
  (NO editar el cache JSON a mano).
- Cada commit es atomico, deja `pnpm exec biome check` + `pnpm exec tsc`
  + `pnpm exec astro check` en verde.
- El ultimo commit elimina `docs/specs/cv-projects-restructure/`.
- El gate de cierre es la bateria de [08](08-verificacion-e2e.md):
  push y PR SOLO con todo en verde.

## 1. Contexto / Problema

El catalogo de proyectos del CV tiene 6 entries (cv-builder, destacame-credit-mexico,
destacame-debt-chile, faststruct, mvp-template-full-stack, portfolio-astro)
de las cuales 2 (cv-builder, portfolio-astro) ya no representan trabajo
relevante del portfolio. La data se sembra en Neon via los YAML de
`serverless/lambda/services/db/core/seeds/data/projects/*.yaml`.

Problemas concretos a resolver:

1. **Curacion de proyectos**: solo 4 proyectos deben aparecer, en orden
   especifico (Chile -> Mexico -> MVP -> FastStruct), con niches curados.
2. **3 URLs en Pago Chile**: el proyecto del sistema de saldar deudas
   tiene 3 sitios en produccion (santander, santanderconsumer, scotiabank);
   `ProjectSchema` solo soporta 1 `url`.
3. **Casos de estudio en el home**: hoy `CaseStudyExpander` aparece como
   bloque expandible bajo el grid de proyectos en CADA pagina del CV.
   Sobrecarga el home; deberia vivir en `/projects/<slug>`.
4. **"Otras vistas" abre tab nueva**: el item del Nav tiene `external:true`
   en `define-site-config.ts` y apunta solo al hub. Se quiere un dropdown
   con los 5 niches y navegacion en la misma pestana.
5. **Hub hero intro**: el parrafo de bienvenida es muy largo y el fondo
   no es full-bleed como los demas niches.
6. **`/track` devuelve 403 en dev**: probable IP blacklist en DynamoDB
   por testing previo con bot-detection, o IP rule sin TTL expirado.
7. **Experiences sin summary**: el home de cada niche muestra
   responsibilities completos (3-5 bullets). Es demasiado denso para una
   timeline. Falta un `summary` corto bilingue y mover el detalle al
   page `/experience/<slug>`.

## 2. Solucion propuesta

### Decisiones clave

- **Decision 1**: Eliminar `cv-builder.yaml` y `portfolio-astro.yaml` de
  seeds. — Razon: el usuario los considera obsoletos y solo quiere 4
  proyectos curados.
- **Decision 2**: Orden global Chile->Mexico->MVP->FastStruct se logra
  con `priority` decreciente (100/90/80/70). El sort dentro de cada
  niche usa este campo. — Razon: no requiere logica nueva de
  ordenamiento, solo data correcta.
- **Decision 3**: Extender `ProjectSchema` con campo opcional
  `links?: Array<{ label: BiLang; url: string }>`. — Razon: el schema
  actual solo tiene `url?: string`; modelar 3 sitios en `description` o
  `caseStudy` es texto, no botones clickables. La extension es
  retro-compatible (campo opcional).
- **Decision 4**: Eliminar el bloque `CaseStudyExpander` del
  `CvSections.astro` y agregar el render de `caseStudyDetailed` (acordeon
  colapsado) en `ProjectDetail.astro`. — Razon: el home queda mas limpio,
  los casos de estudio viven en su contexto natural (el detail del
  proyecto al que pertenecen).
- **Decision 5**: Reemplazar el Nav item "Otras vistas" (link unico al
  hub con `external:true`) por un componente `NicheDropdown.astro` con
  las 5 niches. — Razon: el usuario pidio dropdown interno; navegacion
  cross-subdomain (en la misma pestana) usando `SITE_URLS` por niche y
  detectando el entorno (local/dev/stage/prod).
- **Decision 6**: Hub hero intro: full-bleed background del `<p>` via
  contenedor que extienda 100vw + reducir el texto del `heroIntro` a
  140-180 chars y bajar `text-body-lg` -> `text-body`. — Razon: el bug
  del usuario es visual (no llena el ancho, fuente muy grande), no
  funcional.
- **Decision 7**: Investigar `/track` antes de aplicar fix. Causa
  probable: IP del usuario blacklisteada en tabla DynamoDB
  `portfolio-rate-limit-rules-dev` por testing previo. Fix dependiente.
- **Decision 8**: Agregar `summary: BiLangSchema` (obligatorio) en
  `ExperienceSchema` + a los 9 YAMLs de experiences. Render en home
  reemplaza el listado de responsibilities por el summary; el detail
  page sigue mostrando responsibilities + achievements completos. — Yo
  escribo los 9 summaries (80-140 chars cada uno) basado en el contenido
  existente de cada YAML.

## 3. Criterios de aceptacion (BDD)

- **AC-1**: Given el seed del CV ejecutado en `dev`, When se consulta
  `/cv` a la Lambda CV, Then devuelve exactamente 4 proyectos en este
  orden: `destacame-debt-chile`, `destacame-credit-mexico`,
  `mvp-template-full-stack`, `faststruct`.
- **AC-2**: Given un usuario visita `/` en cualquier niche que incluya
  el proyecto `destacame-debt-chile`, When el `ProjectBentoCard`
  renderiza, Then muestra 3 botones (Santander, Santander Consumer,
  Scotiabank), uno por entrada en `links[]`.
- **AC-3**: Given un usuario visita `/projects/<slug>` de cualquier
  proyecto con `caseStudyDetailed`, When la pagina renderiza, Then
  muestra un bloque acordeon con `problem/process/result` colapsado por
  defecto.
- **AC-4**: Given un usuario visita `/`, When inspecciona el DOM, Then
  NO existe el elemento `.case-studies` en `CvSections.astro` (la
  seccion fue movida al detail).
- **AC-5**: Given un usuario en una niche cualquiera, When hace click
  en el item del Nav que reemplaza "Otras vistas", Then se abre un
  dropdown con 5 entradas (fintech, architect, leader, vibe, generic);
  cada entrada navega en la MISMA pestana al niche correspondiente.
- **AC-6**: Given un usuario en `hub.portfolio.dev.the-full-stack.com`,
  When la pagina renderiza, Then el background del parrafo
  `heroIntro` ocupa 100vw (full-bleed) y el texto tiene menos de 180
  caracteres.
- **AC-7**: Given un usuario en `/` con tracking habilitado, When el
  cliente envia un evento POST a `/track`, Then el endpoint responde
  204 (No Content), NO 403.
- **AC-8**: Given el seed ejecutado, When se carga la pagina `/` de
  cualquier niche, Then cada `TimelineItem` de experience muestra
  `summary[locale]` (1-2 frases), NO el listado completo de
  responsibilities.
- **AC-9**: Given un usuario visita `/experience/<slug>`, When la
  pagina renderiza, Then muestra responsibilities + achievements
  completos (igual que hoy, no cambia el detail page).
- **AC-10**: Given los 4 YAMLs de proyectos seedeados, When se ejecuta
  `pnpm --filter @portfolio/content exec vitest run`, Then todos los
  tests del schema pasan sin errores.

## 4. Diagrama de flujo

N/A — el cambio no altera flujos de control. Es refactor de data + UI +
fix puntual de un endpoint backend.

## 5. Diagrama ER

N/A — los proyectos y experiences en Neon ya tienen tabla. Los nuevos
campos (`summary` en experience, `links` en project) son JSONB. No hay
migracion Alembic nueva porque `summary` y `links` ya estan modelados
como JSONB en las tablas existentes (ver
`serverless/lambda/shared/db/models/cv_project.py` y
`cv_experience.py`); el cambio es solo de datos sembrados.

## 6. Tests requeridos

### 6.B. Unit tests (Vitest)

- `packages/content/tests/schemas.test.ts` (si existe): agregar test que
  valida ProjectSchema con `links[]` y ExperienceSchema con `summary`.
- `packages/content/tests/data/projects.test.ts`: validar que las 4
  entries del cache renderizan correctamente y que los 2 eliminados ya
  no aparecen.

### 6.C. Typecheck

- `pnpm exec tsc --noEmit` recursivo en packages + apps.
- `pnpm exec astro check` por app modificada.

## 7. Archivos afectados

### Crear

- `docs/specs/cv-projects-restructure/{README,01-data-changes,02-ui-changes,03-nav-and-hub,04-experiences,05-track-fix,06-commits,07-paralelizacion,08-verificacion-e2e}.md` — esta spec.
  - Verificar: archivos existen y el README linkea a cada subdoc.
- `packages/ui/src/components/NicheDropdown.astro` — dropdown nuevo con 5 niches.
  - Verificar: `pnpm --filter @portfolio/ui run typecheck`.
- `packages/ui/src/components/ProjectLinksGroup.astro` — render del campo `links[]` como botones.
  - Verificar: idem.

### Modificar

- `packages/content/src/schemas.ts` — extender ProjectSchema con `links[]` y ExperienceSchema con `summary`.
  - Verificar: `pnpm --filter @portfolio/content exec vitest run`.
- `packages/content/src/data/i18n/elements/elements.{es,en}.yaml` — renombrar "Proyectos destacados" -> "Proyectos" (y "Featured projects" -> "Projects").
  - Verificar: `pnpm exec biome check .` y build de cualquier app.
- `packages/cv-pdf/src/lib/render-cv-html.ts` — mismo rename en el render del PDF.
  - Verificar: build del package.
- `serverless/lambda/services/db/core/seeds/data/projects/destacame-debt-chile.yaml` — agregar `links[]`, ajustar niches y priority.
  - Verificar: `serverless run --lambda=db --event=events/seed.json --stage=dev`.
- `serverless/lambda/services/db/core/seeds/data/projects/destacame-credit-mexico.yaml` — ajustar niches y priority.
- `serverless/lambda/services/db/core/seeds/data/projects/mvp-template-full-stack.yaml` — actualizar url a `https://the-full-stack.com/`, niches=[architect,vibe,generic], priority.
- `serverless/lambda/services/db/core/seeds/data/projects/faststruct.yaml` — niches=[vibe,generic], priority.
- `serverless/lambda/services/db/core/seeds/data/experiences/*.yaml` (9 archivos) — agregar campo `summary: { es, en }`.
- `packages/content/src/data-cache/{projects,experiences}.json` — regenerados desde el seed dev.
- `packages/app-shared/src/components/CvSections.astro` — eliminar bloque `.case-studies` (lineas 335-358).
- `packages/app-shared/src/components/ProjectDetail.astro` — agregar render de `caseStudyDetailed` colapsable.
- `packages/ui/src/components/ProjectsBento.astro` — cambiar default `ariaLabel='Proyectos destacados'` -> `'Proyectos'`.
- `packages/ui/src/components/ProjectBentoCard.astro` — soportar `links[]` ademas de `url`/`repo`.
- `packages/ui/src/components/TimelineItem.astro` — recibir `summary` y mostrarlo en home (compacto).
- `packages/app-shared/src/components/CvSections.astro` (TimelineItem region) — pasar `summary` y dejar de pasar responsibilities/achievements completos al home.
- `packages/app-shared/src/lib/define-site-config.ts` — quitar el item "Otras vistas" externo y dejar que Nav use el nuevo `NicheDropdown`.
- `packages/ui/src/components/Nav.astro` — soportar item tipo `dropdown` (renderizar `NicheDropdown`).
- `apps/hub/src/pages/index.astro` — full-bleed del intro + reducir texto.
- `packages/content/src/data/i18n/hub-selector/{es,en}.yaml` — recortar `heroIntro`.
- `serverless/lambda/services/tracking_pixel/manifest.yaml` — ajustar `CORS_ALLOWED_ORIGINS` si aplica.

### Eliminar

- `serverless/lambda/services/db/core/seeds/data/projects/cv-builder.yaml` — proyecto obsoleto.
- `serverless/lambda/services/db/core/seeds/data/projects/portfolio-astro.yaml` — proyecto obsoleto.
- `packages/app-shared/src/components/CvSections.astro` linea 335-358 (bloque `.case-studies` y el import de `CaseStudyExpander` si queda huerfano).

## 12. Validacion y Definition of Done

### Pre-implementacion

- [x] AC numerados (AC-1..AC-10)
- [x] Decisiones del usuario confirmadas (3 preguntas en chat)
- [x] Cache del CV regenerable con `scripts/fetch-cv-cache.mjs`
- [x] Rama `feature/cv-projects-restructure` creada
- [x] No hay breaking changes en APIs publicas (campos nuevos opcionales en
      Project, obligatorio en Experience — todos los YAMLs se actualizan)

### Definition of Done

- [ ] AC-1..AC-10 verificados con tests o inspeccion manual
- [ ] Coverage >=80% per-file en archivos modificados/creados
- [ ] `pnpm exec biome check .` sin errores
- [ ] `pnpm exec tsc --noEmit` sin errores
- [ ] `pnpm exec astro check` sin errores en las 6 apps
- [ ] `pnpm run build` exitoso en las 6 apps
- [ ] `/track` responde 204 en dev (curl o navegador)
- [ ] Spec eliminada en el ultimo commit
- [ ] PR `feature/cv-projects-restructure -> dev` abierto y verde
