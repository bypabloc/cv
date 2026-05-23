# Fase 7: Summary en experiences

## Contexto

Cada experience del CV tiene `responsibilities` y `achievements` como
arrays de bullets. El home renderiza un `TimelineItem` por experience y
muestra hasta 3-5 bullets de responsibilities. Es demasiado denso para
una timeline visual; el detail page `/experience/<slug>` ya muestra
todos los bullets.

Decision (del usuario): agregar `summary: BiLangSchema` obligatorio al
schema; el home muestra solo el summary; el detail sigue mostrando todo.

## Cambios

### Schema

Ver [01-data-changes.md](01-data-changes.md) — `ExperienceSchema` gana
`summary: BiLangSchema` obligatorio.

### YAMLs de experiences

9 archivos en `serverless/lambda/services/db/core/seeds/data/experiences/`:

- `cofasa.yaml`
- `corpoelec.yaml`
- `destacame-architect.yaml`
- `destacame-frontend.yaml`
- `dibal.yaml`
- `goodmeal.yaml`
- `iai.yaml`
- `ipasme.yaml`
- `projects-degrees.yaml`

Para cada uno, agregar campo `summary: { es, en }` con 80-140
caracteres derivado del role + company + impacto primario. Yo escribo
los 9 textos basado en el contenido actual del YAML.

Formato de cada summary:

- ES: 1 frase, accion + impacto + tecnologia clave (si aplica)
- EN: traduccion paralela

Ejemplo (destacame-architect.yaml):

```yaml
summary:
  es: "Arquitecto frontend lideré la modernización del stack Vue/Nuxt y orquesté microservicios fintech para Chile y México."
  en: "Frontend Architect leading the Vue/Nuxt stack modernization and orchestrating fintech microservices for Chile and Mexico."
```

### Render en home (TimelineItem.astro)

Archivo: `packages/ui/src/components/TimelineItem.astro`

Cambios:

1. Aceptar nueva prop `summary?: string` (ya resuelto por locale).
2. Si `summary` esta presente: renderizar solo `<p class="timeline-summary">{summary}</p>` en lugar del listado de `responsibilities`.
3. Si NO esta presente: caer al render actual de responsibilities (por compatibilidad temporal — todos los YAML eventualmente tendran summary).

### Update en CvSections.astro

Archivo: `packages/app-shared/src/components/CvSections.astro:231-294`

Pasar `summary={exp.summary[locale]}` al `TimelineItem` y dejar de
pasar el array de responsibilities (que ya no se renderiza en home).

### Detail page sin cambios

`packages/app-shared/src/components/ExperienceDetail.astro` sigue
mostrando todo (responsibilities + achievements completos). NO se
toca.

## Verificacion

```bash
# 1. Schema valido
pnpm --filter @portfolio/content exec vitest run

# 2. Cada YAML pasa el seed (validacion Pydantic en la Lambda db)
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=serverless/lambda/services/db/events/seed.json \
  --aws-profile=tfs-dev

# 3. El cache regenerado tiene summary en cada experience
node scripts/fetch-cv-cache.mjs
cat packages/content/src/data-cache/experiences.json | jq '.[0].summary'

# 4. Build de las 6 apps
pnpm run build

# 5. Visual: home muestra summary corto, detail muestra todo
pnpm --filter @portfolio/fintech run dev
# abrir http://fintech.localhost:9970 -> seccion experiencia -> deberia mostrar resumenes
# abrir http://fintech.localhost:9970/experience/destacame-architect -> debe mostrar todo
```
