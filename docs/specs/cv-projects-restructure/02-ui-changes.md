# Fase 4: UI de proyectos + casos de estudio

> Cambios en componentes Astro para reflejar el nuevo modelo de datos y
> mover los casos de estudio al detail page.

## 4.1 Renombrar "Proyectos destacados" -> "Proyectos"

Cinco archivos a tocar (todos con el mismo find-and-replace):

| Archivo | Cambio |
|---------|--------|
| `packages/content/src/data/i18n/elements/elements.es.yaml:38` | `title: "Proyectos destacados"` -> `title: "Proyectos"` |
| `packages/content/src/data/i18n/elements/elements.en.yaml:38` | `title: "Featured projects"` -> `title: "Projects"` |
| `packages/ui/src/components/ProjectsBento.astro:10,22` | JSDoc y default de prop -> `'Proyectos'` |
| `packages/cv-pdf/src/lib/render-cv-html.ts:49` | `projects: 'Proyectos destacados'` -> `projects: 'Proyectos'` |
| (cualquier otro match — usar grep) | mismo cambio |

Verificacion: `grep -rn "destacados" packages/ apps/` no debe devolver nada
en archivos de codigo o UI (solo en i18n YAML de curriculum, que son
copys diferentes y se preservan).

## 4.2 Mover casos de estudio: home -> project detail

### A. CvSections.astro: eliminar bloque

Archivo: `packages/app-shared/src/components/CvSections.astro`

Eliminar el bloque lineas 335-358:

```astro
  {
    projs.filter((p) => p.caseStudyDetailed).length > 0 && (
      <div class="case-studies">
        {projs.filter((p) => p.caseStudyDetailed).map((p) => (
          <CaseStudyExpander ... />
        ))}
      </div>
    )
  }
```

Tambien eliminar el `import { CaseStudyExpander }` si queda huerfano.

### B. ProjectDetail.astro: agregar render de caseStudyDetailed

Archivo: `packages/app-shared/src/components/ProjectDetail.astro`

Agregar (despues del bloque de stack o description) un acordeon
colapsado con `problem/process/result + metrics`. Usar el componente
existente `CaseStudyExpander` (vive en `packages/ui/src/components/`).
Asi reutilizamos toda la logica de a11y / animacion.

```astro
{
  project.caseStudyDetailed && (
    <section class="case-study">
      <h2>{t.labels.caseStudyCta}</h2>
      <CaseStudyExpander
        title={project.name}
        problem={project.caseStudyDetailed.problem[locale]}
        process={project.caseStudyDetailed.process[locale]}
        result={project.caseStudyDetailed.result[locale]}
        metrics={project.metrics ? Object.values(project.metrics) : []}
        labels={{ ... }}
      />
    </section>
  )
}
```

Sin cambios en `CaseStudyExpander.astro` mismo (sigue siendo un
`<details>` nativo que arranca colapsado).

## 4.3 Render de links[] en ProjectBentoCard y ProjectDetail

### Nuevo componente: ProjectLinksGroup.astro

Archivo nuevo: `packages/ui/src/components/ProjectLinksGroup.astro`

```astro
---
interface Link {
  label: string  // ya resuelto por locale
  url: string
}

interface Props {
  links?: Link[]
  url?: string
  repo?: string
  fallbackUrlLabel: string  // i18n "Ver sitio" / "View site"
  repoLabel: string         // i18n "Repositorio" / "Repository"
}

const { links, url, repo, fallbackUrlLabel, repoLabel } = Astro.props
const hasLinks = links && links.length > 0
---

{
  hasLinks ? (
    <ul class="project-links">
      {links!.map((l) => (
        <li>
          <a href={l.url} class="link-chip">{l.label}</a>
        </li>
      ))}
      {repo && <li><a href={repo} class="link-chip link-chip--repo">{repoLabel}</a></li>}
    </ul>
  ) : (
    <ul class="project-links">
      {url && <li><a href={url} class="link-chip">{fallbackUrlLabel}</a></li>}
      {repo && <li><a href={repo} class="link-chip link-chip--repo">{repoLabel}</a></li>}
    </ul>
  )
}
```

Estilos: chips compactos (background `--color-surface-2`, border
`--color-border`, padding sm). Reusable en `ProjectBentoCard` y
`ProjectDetail`.

### Integracion en ProjectBentoCard.astro

Reemplazar el render de `url`/`repo` (lineas ~50-80) por el nuevo
`ProjectLinksGroup`. Aceptar `links?: ProjectLink[]` como nueva prop y
forwardearlo.

### Integracion en ProjectDetail.astro

Mismo cambio: usar `ProjectLinksGroup` para mostrar los links
(separados visualmente del case study).

## Strings i18n nuevos

En `packages/content/src/data/i18n/elements/elements.{es,en}.yaml`,
agregar dentro de `labels`:

```yaml
# es
viewSite: "Ver sitio"
viewRepo: "Repositorio"

# en
viewSite: "View site"
viewRepo: "Repository"
```

Asegurar que el schema `ElementsStringsSchema.labels` (en `schemas.ts`
linea 467-484) incluye los nuevos campos:

```typescript
labels: z.object({
  // ...
  viewSite: z.string().min(1),
  viewRepo: z.string().min(1),
}),
```

## Verificacion

```bash
# 1. Typecheck del package content (schemas)
pnpm --filter @portfolio/content run typecheck

# 2. Astro check de las 6 apps
pnpm exec astro check

# 3. Build de las 6 apps
pnpm run build

# 4. Visual: levantar dev en una app y verificar:
#    - "Proyectos" en el titulo (no "destacados")
#    - Card de destacame-debt-chile muestra 3 botones
#    - NO existe bloque .case-studies en el home
#    - /projects/<slug> muestra el acordeon de caseStudyDetailed
pnpm --filter @portfolio/fintech run dev
```
