# 10. View transitions: diseno y referencia de implementacion

> Referencia visual + codigo de los 4 patrones de view transitions acordados.
> Sidecar de los commits 10 y 11 ([06-commits.md](06-commits.md)).

[← 09](09-validacion-done.md) · [README](README.md)

## Decisiones (recap)

| Aspecto | Eleccion |
|---------|----------|
| Page nav default | Fade 300ms (Astro built-in) |
| Shared element 1 | Hero identity (`transition:name='hero-identity'`) |
| Shared element 2 | Project card morph (`transition:name='project-{slug}'`) |
| Shared element 3 | Theme toggle circular clip-path |
| Listas | Stagger 40ms fade + translateY(8px), una vez por lista |
| `prefers-reduced-motion: reduce` | Strict (`navigation: none` + 0.01s) |
| Trigger tracking | `astro:page-load` con guard `firstLoad` |

## Soporte de navegador

| Navegador | Cross-document VT | Same-document VT | Notas |
|-----------|-------------------|------------------|-------|
| Chrome 126+ | si | si | Soporte completo |
| Edge 126+ | si | si | Soporte completo |
| Safari 18.2+ | si | si | Soporte completo (Dec 2024+) |
| Firefox 133+ | NO | si | Same-doc OK; cross-doc esperado 2026 |

Astro 6 + `<ClientRouter />` provee fallback automatico: en navegadores
sin soporte, la navegacion es un hard reload sin animacion.

## Patron 1 — Page nav default (fade 300ms)

`<ClientRouter />` ya emite fade por defecto. NO necesitamos override
salvo para fijar duracion explicita.

### `packages/app-shared/src/layouts/BaseLayout.astro`

```astro
---
import { ClientRouter } from 'astro:transitions'
---
<head>
  <ClientRouter />
  <!-- ... -->
</head>
```

### CSS global (en `packages/ui/src/styles/view-transitions.css`)

```css
/* Page-level fade explicito (300ms ease-in-out) */
::view-transition-old(root),
::view-transition-new(root) {
  animation-duration: 300ms;
  animation-timing-function: ease-in-out;
}
```

## Patron 2 — Hero identity flying

El bloque del hero (nombre + role) comparte identidad entre paginas. Si
ambas pages tienen un elemento con `transition:name='hero-identity'`, el
browser lo morphea (posicion, escala, opacidad) en lugar de fade.

### Donde aplicarlo

| App | Pages con hero identity |
|-----|-------------------------|
| `generic` | `/`, `/about`, `/experience` |
| `hub` | `/` (solo home; no hay /about) |
| `fintech` | `/`, `/about` |
| `architect` | `/`, `/about` |
| `leader` | `/`, `/about` |
| `vibe` | `/`, `/about` |

### Codigo (snippet)

```astro
---
// packages/app-shared/src/components/HeroIdentity.astro
interface Props {
  name: string
  role: string
  variant?: 'large' | 'compact'
}
const { name, role, variant = 'large' } = Astro.props
---
<div class:list={['hero-identity', variant]} transition:name="hero-identity">
  <h1>{name}</h1>
  <p>{role}</p>
</div>

<style>
  .hero-identity { /* tokens del DS */ }
  .hero-identity.compact h1 { font-size: var(--font-size-32); }
</style>
```

> El navegador morphea AUTOMATICAMENTE entre `large` y `compact`: el
> `transition:name` casa los dos elementos, FLIP-style. NO hay que
> escribir keyframes.

## Patron 3 — Project card → detalle

Cada `ProjectCard.astro` declara `transition:name='project-{slug}'`. La
pagina de detalle (`/projects/[slug].astro`) declara el MISMO name en su
hero. El browser anima la expansion automaticamente.

### `packages/app-shared/src/components/ProjectCard.astro`

```astro
---
interface Props {
  slug: string
  title: string
  thumbnail: string
}
const { slug, title, thumbnail } = Astro.props
const transitionName = `project-${slug}`
---
<a href={`/projects/${slug}`} class="project-card">
  <img src={thumbnail} alt="" transition:name={transitionName} />
  <h3>{title}</h3>
</a>
```

### `apps/<app>/src/pages/projects/[slug].astro`

```astro
---
const { slug } = Astro.params
const project = await getProject(slug)
---
<article>
  <header>
    <img src={project.heroImage} alt="" transition:name={`project-${slug}`} />
    <h1>{project.title}</h1>
  </header>
  <!-- contenido -->
</article>
```

### Gotcha de scope

- `transition:name` debe ser UNICO por DOM. Si dos `ProjectCard`s con el
  mismo slug aparecen en la misma pagina, falla silenciosamente.
- Solucion: prefijar con `niche` si el listing se reutiliza:
  `transition:name={`project-${niche}-${slug}`}`. Para este plan, los
  proyectos son distintos por niche → seguro con solo slug.

### Apps con pages de detalle

| App | `/projects/[slug]` existe |
|-----|---------------------------|
| `generic` | si |
| `hub` | no (graceful degradation: cards sin `transition:name`) |
| `fintech` | si |
| `architect` | si |
| `leader` | no |
| `vibe` | si |

En las apps sin pages de detalle (`hub`, `leader`), los `ProjectCard`
omiten `transition:name`. Sin colisiones, sin morphs huerfanos.

## Patron 4 — Theme toggle circular clip-path

Cuando se cambia dark/light, el nuevo tema "crece" desde la posicion del
toggle button con clip-path circular. Firefox cae a cross-fade automatico
(no soporta clip-path en view-transitions todavia).

### `packages/ui/src/components/ThemeToggle.astro`

```astro
---
// El componente ya existe; agregamos el script del custom transition.
---
<button id="theme-toggle" aria-label="Toggle theme">
  <!-- icon -->
</button>

<script>
const button = document.querySelector('#theme-toggle')!

button.addEventListener('click', async (event) => {
  // Obtener coordenadas del click para el origen del circulo
  const x = (event as PointerEvent).clientX
  const y = (event as PointerEvent).clientY
  const endRadius = Math.hypot(
    Math.max(x, innerWidth - x),
    Math.max(y, innerHeight - y),
  )

  const isDark = document.documentElement.classList.contains('dark')

  if (!document.startViewTransition || matchMedia('(prefers-reduced-motion: reduce)').matches) {
    // Fallback sin animacion
    document.documentElement.classList.toggle('dark')
    localStorage.setItem('theme', isDark ? 'light' : 'dark')
    return
  }

  const transition = document.startViewTransition(() => {
    document.documentElement.classList.toggle('dark')
    localStorage.setItem('theme', isDark ? 'light' : 'dark')
  })

  await transition.ready

  document.documentElement.animate(
    {
      clipPath: [
        `circle(0px at ${x}px ${y}px)`,
        `circle(${endRadius}px at ${x}px ${y}px)`,
      ],
    },
    {
      duration: 400,
      easing: 'ease-in-out',
      pseudoElement: '::view-transition-new(root)',
    },
  )
})
</script>
```

### Reduced-motion fallback

El script ya hace `early return` cuando `prefers-reduced-motion: reduce`.

## Patron 5 — Stagger fade-in en listas

Cada item de una lista (experiences, projects, skills) aparece con
delay incremental. Solo en la PRIMERA carga (IntersectionObserver +
`once: true`). NO en cada nav.

### `packages/ui/src/lib/stagger.ts` (nuevo)

```typescript
/**
 * @function applyStagger
 * @description Aplica fade-in + translateY con delay incremental a una
 * lista de items, una sola vez cuando entran al viewport.
 * @param container - Elemento padre que contiene los items
 * @param itemSelector - Selector relativo (ej. ':scope > article')
 * @param delayMs - Delay entre items (default 40)
 * @returns IntersectionObserver para que el caller pueda disconnect
 */
export function applyStagger(
  container: Element,
  itemSelector: string,
  delayMs = 40,
): IntersectionObserver {
  const items = container.querySelectorAll<HTMLElement>(itemSelector)
  items.forEach((item, idx) => {
    item.style.setProperty('--stagger-idx', String(idx))
    item.classList.add('stagger-pending')
  })

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('stagger-visible')
        observer.unobserve(entry.target)
      }
    })
  }, { threshold: 0.1 })

  items.forEach((item) => observer.observe(item))
  return observer
}
```

### CSS (en `packages/ui/src/styles/view-transitions.css`)

```css
.stagger-pending {
  opacity: 0;
  transform: translateY(8px);
}

.stagger-visible {
  animation: stagger-in 400ms ease-out forwards;
  animation-delay: calc(var(--stagger-idx, 0) * 40ms);
}

@keyframes stagger-in {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .stagger-pending,
  .stagger-visible {
    opacity: 1;
    transform: none;
    animation: none;
  }
}
```

### Uso en una pagina

```astro
---
// apps/generic/src/pages/experience.astro
import { ExperienceCard } from '@portfolio/app-shared'
---
<section class="experience-list" data-stagger>
  {experiences.map((exp) => <ExperienceCard {...exp} />)}
</section>

<script>
import { applyStagger } from '@portfolio/ui/lib/stagger'

document.addEventListener('astro:page-load', () => {
  document.querySelectorAll<HTMLElement>('[data-stagger]').forEach((el) => {
    applyStagger(el, ':scope > article')
  })
})
</script>
```

## Patron de cierre — `prefers-reduced-motion` strict

Bloque global al inicio de `view-transitions.css`:

```css
@media (prefers-reduced-motion: reduce) {
  @view-transition {
    navigation: none;
  }

  ::view-transition-old(*),
  ::view-transition-new(*) {
    animation-duration: 0.01ms !important;
    animation-delay: 0s !important;
  }
}
```

## Audit de colisiones `transition:name`

Antes del commit 12 (Playwright), correr el audit manual:

```bash
# Buscar TODOS los transition:name del repo
rg -n "transition:name" apps/ packages/ | sort
```

Esperado:
- `hero-identity` aparece en 1 component (`HeroIdentity.astro`), usado
  por las pages que lo importan. Sin colision (mismo name = morph).
- `project-{slug}` es dinamico, computado por slug. Sin colision si los
  slugs son unicos por niche.
- Cero `transition:name` mas en el repo.

Si el audit revela un `transition:name` no listado en este capitulo,
investigar y resolver antes del PR.

## Verificacion E2E especifica (parte del capitulo 08)

```bash
# 1. ClientRouter activo en cada app
for app in generic hub fintech architect leader vibe; do
  rg -l "ClientRouter" apps/$app/src/layouts/ || echo "MISSING: $app"
done

# 2. Sin colisiones (esperar 0 duplicados de hero-identity en una misma page)
pnpm exec playwright test tests/feature/specs/view-transitions.spec.ts

# 3. Reduced-motion respect (visual snapshot con --reduce-motion)
pnpm exec playwright test --grep="reduced-motion" tests/feature/specs/view-transitions.spec.ts
```

## Referencias

- Astro Docs: [View Transitions](https://docs.astro.build/en/guides/view-transitions/)
- MDN: [View Transition API](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API)
- Chrome blog 2025: [What's new in View Transitions](https://developer.chrome.com/blog/view-transitions-in-2025/)
- Akash Hamirwasia: [Full-page theme toggle with View Transitions](https://akashhamirwasia.com/blog/full-page-theme-toggle-animation-with-view-transitions-api/)
- WCAG 2.2: [Pause, Stop, Hide (2.2.2)](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html)

---

Final del plan. Volver al [README](README.md).
