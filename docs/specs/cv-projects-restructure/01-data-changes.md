# Fase 1-3: Schemas + seeds (data)

> Cambios al schema Zod y a los YAML de seeds del CV. Producen el cambio
> de data renderizable por las apps (post-regeneracion del cache).

## Cambios al schema (packages/content/src/schemas.ts)

### ProjectSchema

Agregar campo opcional `links`:

```typescript
export const ProjectLinkSchema = z.object({
  label: BiLangSchema,
  url: z.string().url(),
})
export type ProjectLink = z.infer<typeof ProjectLinkSchema>

export const ProjectSchema = z.object({
  // ... campos existentes
  links: z.array(ProjectLinkSchema).max(5).optional(),
  // ...
})
```

Reglas:

- `links` es OPCIONAL. Los proyectos con 1 sola URL siguen usando `url`.
- Si `links` esta presente, la UI muestra los multiples botones; `url`
  puede coexistir como URL principal (la primera del array, idealmente).
- Maximo 5 items para evitar UI saturada.

### ExperienceSchema

Agregar campo OBLIGATORIO `summary`:

```typescript
export const ExperienceSchema = z.object({
  // ... campos existentes
  summary: BiLangSchema,
  // ...
})
```

Nota: es obligatorio porque toda experience debe poder renderizarse en
home con un resumen corto. Los 9 YAMLs deben tener este campo antes del
seed.

## Eliminacion de proyectos obsoletos

Eliminar:

- `serverless/lambda/services/db/core/seeds/data/projects/cv-builder.yaml`
- `serverless/lambda/services/db/core/seeds/data/projects/portfolio-astro.yaml`

Verificacion post-eliminacion:

```bash
ls serverless/lambda/services/db/core/seeds/data/projects/
# debe mostrar exactamente 4 archivos
```

## Reescritura de los 4 proyectos

### destacame-debt-chile.yaml (priority maxima: 100/90/85/70)

- `url`: `https://pagaloaqui.cl/santander` (URL principal del array)
- `links`:
  - `{ label: { es: "Santander", en: "Santander" }, url: "https://pagaloaqui.cl/santander" }`
  - `{ label: { es: "Santander Consumer", en: "Santander Consumer" }, url: "https://pagaloaqui.cl/santanderconsumer" }`
  - `{ label: { es: "Scotiabank", en: "Scotiabank" }, url: "https://solucionesscotiabank.pagaloaqui.cl" }`
- `niches`: `[fintech, leader, architect, generic]`
- `priority`: `{ fintech: 100, leader: 100, architect: 95, generic: 85 }`
- Mantener `summary`, `description`, `caseStudy`, `caseStudyDetailed`,
  `metrics`, `stack`, `isConfidential: true`, `projectType: fintech-platform`.

### destacame-credit-mexico.yaml (priority 90)

- `url`: `https://www.destacame.com.mx/`
- `niches`: `[fintech, leader, generic]`
- `priority`: `{ fintech: 90, leader: 95, generic: 80 }`
- Resto sin cambios (texto del summary/case study es bueno hoy).

### mvp-template-full-stack.yaml (priority 80)

- `url`: `https://the-full-stack.com/` (URL del usuario)
- `repo`: `https://github.com/bypabloc/cv` (repo del usuario)
- `niches`: `[architect, vibe, generic]` (sin `hub` porque `hub` no esta en NICHES — ver schemas)
- `priority`: `{ architect: 80, vibe: 90, generic: 75 }`
- Actualizar `summary` y `description` para reflejar que es ESTE
  portfolio (Astro 6 + serverless backend + devtools CLI + Claude Code
  harness), no el repo `bypabloc/mvp-template-full-stack` viejo.

NOTA: `hub` NO es un niche en `NICHES` (revisar `schemas.ts` linea 14-20).
El hub solo es la app selector; los proyectos no se filtran por hub
porque hub no muestra `CvSections`. Asi que ignorar "hub" en niches y
quedarse con los 5 niches reales.

### faststruct.yaml (priority 70)

- `url`: `https://marketplace.visualstudio.com/items?itemName=the-full-stack.faststruct`
- `niches`: `[vibe, generic]`
- `priority`: `{ vibe: 80, generic: 65 }`
- Mantener resto del contenido (ya esta correcto).

## Comando de seed (despues de editar YAMLs)

```bash
# Aplicar seed en dev
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=serverless/lambda/services/db/events/seed.json \
  --aws-profile=tfs-dev

# Regenerar cache JSON desde Neon
node scripts/fetch-cv-cache.mjs

# Commitear el cache regenerado junto con los seeds
git add packages/content/src/data-cache/ \
        serverless/lambda/services/db/core/seeds/data/
```

## Verificacion

```bash
# 1. Schema valido
pnpm --filter @portfolio/content run typecheck

# 2. Vitest pasa con la nueva data
pnpm --filter @portfolio/content exec vitest run

# 3. Astro check de las 6 apps (consume el cache)
pnpm exec astro check
```

Si vitest falla por shape de los YAMLs, corregir el YAML mas el cache.
