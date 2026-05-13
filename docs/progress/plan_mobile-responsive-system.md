# Plan: Sistema responsivo + redisenio mobile del portfolio

> Scope: Large (>11 archivos). Sistema de breakpoints Tailwind-standard,
> refactor mobile-first de packages compartidos, hamburger drawer con
> `<dialog>`, propagacion a las 6 apps, verificacion con Playwright
> screenshots en 3 viewports.

## 1. Contexto / Problema

El portfolio actual (6 apps Astro + 5 packages compartidos) se ve roto
en mobile (<640px). Los problemas concretos detectados via exploracion:

- **Sin sistema de breakpoints**: cada componente hardcodea `@media
  (max-width: 640px)` o `600px` o `960px` con valores arbitrarios. No hay
  tokens (`--bp-sm`, `--bp-md`, ...) en `tokens.css`. 11+ media queries
  duplicadas en `packages/ui/src/components/`.
- **Approach max-width pragmatico**: el CSS base es desktop, los overrides
  son `@media (max-width: ...)`. Esto rompe el principio mobile-first y
  produce reglas peleando entre si.
- **Nav.astro sin drawer**: en mobile solo achica `gap` y `font-size`; los
  items siguen inline horizontal. Con 4+ items + locale + theme-toggle,
  hay overflow horizontal a 320-375px.
- **`.container-wide` con padding fijo**: `padding-inline: var(--space-24)`
  (24px) siempre. En mobile <360px el contenido toca los bordes.
- **HeroImpact**: `display-mega` clamp ya es fluido pero `padding-block:
  var(--space-100)` (100px) es excesivo a <640px; el `headline` con
  `max-width: 14ch` rompe en 320px.
- **ProjectsBento / SkillsGrid**: grids sin fallback a 1 columna explicito,
  cards bento de tamanio fijo que producen scroll horizontal.
- **No hay menu mobile**: no existe boton hamburger, drawer, ni focus trap.

### Hallazgos de exploracion

- Existen `--font-size-display-*` con `clamp(...)` (fluidos), pero solo
  cubren tipografia, no spacing ni layout.
- Cada app tiene 3 paginas (`index`, `about`, `certificates`) + variante
  `en/`. Total: 18 paginas concretas + hub (1).
- `tests/feature/smoke/cv-screenshots.spec.ts` ya captura screenshots en
  desktop; solo falta extender a viewports mobile + tablet.
- Tailwind v4 esta disponible via `@tailwindcss/vite` + `@theme inline` en
  `global.css` — ya hay infraestructura para mapear breakpoints como
  tokens consumibles por utilities.

## 2. Solucion Propuesta

Sistema de breakpoints Tailwind-standard (5 puntos: sm/md/lg/xl/2xl)
expuestos como CSS variables, refactor mobile-first de los componentes
compartidos, hamburger drawer con `<dialog>` HTML5 + JS minimo, container
con padding fluido via `clamp()`, y propagacion a las 6 apps con
verificacion Playwright screenshots en mobile (375px) + tablet (768px) +
desktop (1280px).

### Decisiones clave

- **Decision 1: Breakpoints Tailwind-standard (sm=640, md=768, lg=1024,
  xl=1280, 2xl=1536)** — match con Tailwind v4 ya en uso, ecosistema
  ampliamente documentado, y permite combinar utilities Tailwind con
  media queries custom sin desalineacion.
- **Decision 2: Mobile-first refactor (`@media (min-width)`)** — el CSS
  base se reescribe pensado para 320-639px; cada breakpoint agrega
  progresivamente. Anti-pattern del approach `max-width` (deuda tecnica,
  reglas peleandose) queda eliminado.
- **Decision 3: Tokens CSS variables para breakpoints** — `--bp-sm: 640px`
  etc. en `tokens.css`. Aunque CSS no permite usar variables en media
  queries directamente (limitacion del estandar), los tokens sirven como
  documentacion + son consumibles por JS (`getComputedStyle`) para sync
  con `matchMedia` cuando se necesite (drawer toggle).
- **Decision 4: `<dialog>` nativo para drawer** — popover API tiene soporte
  Baseline 2024 pero menos control sobre animaciones; `<dialog>` da focus
  trap + escape key + backdrop nativos. JS minimo (~40 lineas) en
  `packages/ui/src/lib/mobile-nav.ts`.
- **Decision 5: Container padding fluido con `clamp()`** —
  `padding-inline: clamp(1rem, 4vw, 1.5rem)` reemplaza `var(--space-24)`.
  Mantiene 16px minimo en 320px y crece a 24px en desktop.
- **Decision 6: 3 viewports en cv-screenshots** — 375x812 (iPhone 13),
  768x1024 (iPad portrait), 1280x800 (desktop). 6 apps x 3 viewports x
  3 scroll positions = 54 screenshots. Suficiente evidencia visual sin
  explotar tiempo de CI/feature run.
- **Decision 7: Minimo soportado 320px** — iPhone SE, cubre 99% mercado.
  Headlines con `clamp()` deben caber sin scroll horizontal.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given un usuario en mobile 320px, When carga cualquier
  pagina de las 6 apps, Then no hay scroll horizontal y todo el contenido
  cabe en el viewport.
- **AC-2**: Given un usuario en mobile <768px, When ve el Nav, Then el
  Nav muestra solo brand + boton hamburger + theme-toggle (sin items
  inline ni locale switcher inline).
- **AC-3**: Given un usuario en mobile <768px, When toca el boton
  hamburger, Then se abre un drawer con focus trap, items de menu, locale
  switcher y boton cerrar; presionar Esc o tocar backdrop lo cierra.
- **AC-4**: Given un usuario en tablet >=768px y <1024px, When ve el
  layout, Then el Nav muestra los items inline y los grids con 2
  columnas (proyectos, skills, awards).
- **AC-5**: Given un usuario en desktop >=1024px, When ve el layout,
  Then funciona identico al diseno actual desktop (no hay regresion
  visual).
- **AC-6**: Given el `HeroImpact` renderizado en mobile 320-639px, When
  inspecciono, Then el `padding-block` se reduce a `clamp(2rem, 8vw,
  3rem)` y el headline cabe sin overflow.
- **AC-7**: Given `tokens.css`, When hago `getComputedStyle`, Then expone
  `--bp-sm: 640px`, `--bp-md: 768px`, `--bp-lg: 1024px`, `--bp-xl: 1280px`,
  `--bp-2xl: 1536px`.
- **AC-8**: Given una pagina con animaciones, When el usuario tiene
  `prefers-reduced-motion: reduce`, Then el drawer abre/cierra sin
  transicion (alineado con scroll-driven.css existente).
- **AC-9**: Given los hooks pre-push del proyecto, When corro `pnpm run
  build`, Then las 6 apps buildean sin errores en `dist/`.
- **AC-10**: Given los screenshots Playwright, When ejecuto
  `cv-screenshots.spec.ts` en 3 viewports, Then se generan 54 screenshots
  (6 apps x 3 viewports x 3 scrolls) sin overflow horizontal en ninguna.

## 4. Diagrama de Flujo (Antes y Despues)

### Antes (Nav en mobile)

```
[brand]  [item1] [item2] [item3] [item4]  [EN] [theme]
                                                      ^
                                                      overflow horizontal
                                                      en <640px
```

### Despues (Nav en mobile <768px)

```
[brand]                                  [theme] [hamburger]
                                                       |
                                                       v toca
+-----------------+
| <dialog drawer> |
| [X cerrar]      |
| ----            |
| item1           |
| item2           |
| item3           |
| item4           |
| ----            |
| [ES] [EN]       |
+-----------------+
| backdrop dim    |
```

### Antes (cv-screenshots)

```
6 apps -> 1 viewport (desktop 1280x800) -> 3 scrolls = 18 screenshots
```

### Despues (cv-screenshots)

```
6 apps -> 3 viewports (375, 768, 1280) -> 3 scrolls = 54 screenshots
```

## 5. Diagrama ER

N/A — no hay cambios en content collections ni schemas Zod. El sistema
responsivo es 100% CSS + un componente Astro (drawer).

## 6. Tests Requeridos

### 6.A. TDD flows (logica nueva en `packages/ui/src/lib/`)

- WHEN llamo `initMobileNav()` THEN se monta listener en `[data-mobile-nav-toggle]` y retorna funcion cleanup [AC-3]
- WHEN el usuario toca toggle Y dialog no esta abierto THEN se invoca `dialog.showModal()` [AC-3]
- WHEN el usuario presiona Esc dentro del dialog THEN se invoca `dialog.close()` (manejado nativo, validar no-error) [AC-3]
- WHEN el usuario tiene `prefers-reduced-motion: reduce` THEN el dialog se renderiza con `transition: none` (validar via `matchMedia` mock) [AC-8]

### 6.B. Unit tests (Vitest)

Path mirroring obligatorio. Coverage v8 >= 80% per-file.

- `packages/ui/src/lib/mobile-nav.ts` -> `packages/ui/tests/lib/mobile-nav.test.ts`
- `packages/ui/src/components/Nav.astro` -> `packages/ui/tests/components/Nav.test.ts` (testear HTML parseado del modulo)

Mocks:
- `window.matchMedia` (happy-dom no implementa por defecto)
- `HTMLDialogElement.showModal/close` si happy-dom no los soporta nativos
- No mockear: utilities propias, niche-tokens

### 6.C. Typecheck

- `pnpm exec tsc --noEmit` strict en raiz
- `pnpm exec astro check` en cada app (per-package via pnpm filter)
- Falla en pre-push si hay error TS o astro

### 6.D. E2E Tests (Playwright)

Extender `tests/feature/smoke/cv-screenshots.spec.ts`:

- WHEN visito cada una de las 6 apps en viewport 375x812 THEN hero, mid y bottom screenshots no muestran scroll horizontal [AC-1, AC-10]
- WHEN visito cada app en 375x812 Y toco `[data-mobile-nav-toggle]` THEN dialog drawer se abre con `[aria-modal=true]` [AC-3]
- WHEN viewport >= 768px THEN `[data-mobile-nav-toggle]` no es visible (`display: none`) [AC-4]
- WHEN viewport 1280x800 THEN screenshots coinciden visualmente con baseline pre-refactor (regresion 0) [AC-5]

## 7. Archivos Afectados

### Crear

- `packages/ui/src/styles/breakpoints.css` — modulo de breakpoints + utility classes responsive (.hidden-mobile, .only-mobile, .container-fluid)
  - Verificar: `pnpm exec biome check packages/ui/src/styles/breakpoints.css`
  - Verificar: `pnpm run build` exitoso en todas las apps
- `packages/ui/src/lib/mobile-nav.ts` — `initMobileNav()` con cleanup, focus trap auxiliar si dialog no lo da en mobile webkit
  - Verificar: `pnpm exec vitest run packages/ui/tests/lib/mobile-nav.test.ts`
  - Verificar coverage: >= 80% per-file
- `packages/ui/src/components/MobileNavDrawer.astro` — componente `<dialog>` con items + locale + cerrar
  - Verificar: `pnpm exec astro check`
- `packages/ui/tests/lib/mobile-nav.test.ts` — unit tests TDD (red phase primero)
  - Verificar: `pnpm exec vitest run` pasa
- `packages/ui/tests/components/Nav.test.ts` — test del Nav refactorizado (incluye drawer toggle)
  - Verificar: `pnpm exec vitest run` pasa
- `docs/progress/explore_mobile-responsive.md` — bitacora de exploracion (este plan + decisiones)
  - Verificar: existe + linkea a esta planificacion

### Modificar

- `packages/ui/src/styles/tokens.css` — agregar `--bp-sm` ... `--bp-2xl` + `--container-padding-fluid: clamp(1rem, 4vw, 1.5rem)`
  - Verificar: `getComputedStyle(document.documentElement).getPropertyValue('--bp-sm')` retorna `640px` [AC-7]
- `packages/ui/src/styles/global.css` — refactor `.container-*` con padding fluido + import de `breakpoints.css`
  - Verificar: `pnpm run build` + `pnpm run preview` muestra container sin overflow en 320px
- `packages/ui/src/index.ts` — exportar `initMobileNav` y `MobileNavDrawer`
  - Verificar: `pnpm exec tsc --noEmit` sin errores
- `packages/ui/src/components/Nav.astro` — refactor mobile-first: en <768px mostrar solo brand + hamburger + theme, en >=768px mostrar items inline
  - Verificar: `pnpm exec astro check` sin warnings
  - Verificar: viewport 320px no produce scroll horizontal [AC-1, AC-2]
- `packages/ui/src/components/Hero.astro` — refactor mobile-first del `padding-block` y `headline`
  - Verificar: viewport 320px headline cabe sin truncate
- `packages/ui/src/components/HeroImpact.astro` — refactor mobile-first; reemplazar `@media (max-width: 640px)` por base mobile + `@media (min-width: 640px)` para escalar
  - Verificar: viewport 320px headline cabe; viewport 1280px identico a baseline [AC-5, AC-6]
- `packages/ui/src/components/StatsBar.astro` — mobile-first; en <640px grid 1col, >=640px 2col, >=1024px 4col
  - Verificar: viewport 375px no overflow
- `packages/ui/src/components/ExperienceTimeline.astro` — mobile-first; gap + padding reducidos en mobile
  - Verificar: viewport 375px sin overflow
- `packages/ui/src/components/AwardCard.astro` — mobile-first
  - Verificar: viewport 375px card legible
- `packages/ui/src/components/ProjectsBento.astro` — grid 1col en mobile, 2col tablet, 3col desktop (con bento spans variables solo >=lg)
  - Verificar: viewport 375px y 768px sin overflow
- `packages/ui/src/components/ProjectBentoCard.astro` — mobile-first; reset de spans bento en <1024px
  - Verificar: viewport 375px card 1col
- `packages/ui/src/components/SkillsGrid.astro` — mobile-first
  - Verificar: viewport 375px sin overflow
- `packages/ui/src/components/SkillsMarquee.astro` — ajustar velocidad/size en mobile
  - Verificar: viewport 375px marquee visible y readable
- `packages/ui/src/components/Footer.astro` — mobile-first: contacts stack vertical en mobile
  - Verificar: viewport 320px sin overflow
- `packages/ui/src/components/SectionHeader.astro` — mobile-first
  - Verificar: viewport 320px titulo legible
- `packages/ui/src/components/CaseStudyExpander.astro` — mobile-first
  - Verificar: viewport 375px expander funciona
- `packages/ui/src/components/ExperienceCard.astro` — mobile-first
  - Verificar: viewport 375px sin overflow
- `packages/ui/src/components/ProjectCard.astro` — mobile-first
  - Verificar: viewport 320px card legible
- `packages/ui/src/components/ContactLinks.astro` — mobile-first stack vertical
  - Verificar: viewport 320px contacts apilados
- `packages/ui/src/components/NicheBadge.astro` — verificar que no rompe en mobile
  - Verificar: viewport 320px badge inline
- `packages/app-shared/src/components/ArchitectureDiagram.astro` — mobile-first; reemplazar `@media (max-width: 900px)` por mobile-first equivalente
  - Verificar: viewport 375px diagrama legible
- `packages/app-shared/src/components/CvSections.astro` — mobile-first layout
  - Verificar: viewport 375px CV legible
- `packages/app-shared/src/components/AiWorkflowSection.astro` — mobile-first
  - Verificar: viewport 375px legible
- `packages/app-shared/src/components/AtsKeywordsPills.astro` — mobile-first pills wrap
  - Verificar: viewport 320px pills wrappean
- `packages/app-shared/src/components/LeadershipStats.astro` — mobile-first stack
  - Verificar: viewport 320px stats apilados
- `packages/app-shared/src/pages/AboutSection.astro` — verificar pages no rompen
  - Verificar: viewport 375px about legible
- `packages/app-shared/src/pages/CertificatesSection.astro` — mobile-first cert cards
  - Verificar: viewport 375px certs visibles
- `packages/app-shared/src/layouts/SitePageLayout.astro` — agregar wrapper `[data-mobile-nav-host]` para el drawer
  - Verificar: `pnpm exec astro check` sin errores
- `tests/feature/smoke/cv-screenshots.spec.ts` — agregar viewports 375x812, 768x1024, 1280x800 con 3 scrolls cada uno
  - Verificar: `python3 devtools/run.py test_runner --module=feature --type=feature --env=local` genera 54 screenshots
- `apps/{generic,hub,fintech,architect,leader,vibe}/src/pages/index.astro` (x6) — propagar `[data-mobile-nav-host]` si la pagina no usa SitePageLayout (hub es indice especial; verificar)
  - Verificar: `pnpm run build` por app exitoso
- `apps/{generic,fintech,architect,leader,vibe}/src/pages/about.astro` (x5) — sin cambios estructurales, solo verificacion visual
  - Verificar: viewport 375px about legible
- `apps/{generic,fintech,architect,leader,vibe}/src/pages/certificates.astro` (x5) — sin cambios estructurales, solo verificacion visual
  - Verificar: viewport 375px cert legible
- `apps/{generic,fintech,architect,leader,vibe}/src/pages/en/{index,about,certificates}.astro` (x15) — heredan via SitePageLayout, solo verificacion visual
  - Verificar: viewport 375px contenido legible en /en/

### Eliminar

(ninguno — el refactor reemplaza CSS sin borrar archivos)

## 8. Descomposicion para Paralelizacion

Plan Large (>30 archivos). Descomposicion sugerida en 5 tareas
secuenciales mas que paralelizables, dado que la mayoria depende del paso
1 (tokens) y paso 2 (Nav drawer). Solo el paso 3 (componentes de cards y
secciones) es paralelizable internamente.

### Tarea 1 (foundation): tokens + breakpoints CSS

- **Archivos**: `packages/ui/src/styles/tokens.css`, `packages/ui/src/styles/breakpoints.css`, `packages/ui/src/styles/global.css`
- **AC referenciados**: AC-7, AC-1 (parcial)
- **Depende de**: nada
- **Paralelizable con**: ninguna (foundation)
- **Verify**: `pnpm exec biome check .` + `pnpm run build` + test `--bp-sm` expuesto
- **Done**: tokens existen, container fluido, todos los apps siguen buildeando

### Tarea 2 (drawer): mobile nav infrastructure

- **Archivos**: `packages/ui/src/lib/mobile-nav.ts`, `packages/ui/src/components/MobileNavDrawer.astro`, `packages/ui/src/components/Nav.astro`, `packages/ui/src/index.ts`, `packages/ui/tests/lib/mobile-nav.test.ts`, `packages/ui/tests/components/Nav.test.ts`, `packages/app-shared/src/layouts/SitePageLayout.astro`
- **AC referenciados**: AC-2, AC-3, AC-4, AC-8
- **Depende de**: Tarea 1 (necesita `--bp-md` para sync JS/CSS)
- **Paralelizable con**: ninguna (Nav es critico para todas las paginas)
- **Verify**: `pnpm exec vitest run` con coverage >= 80%, drawer abre/cierra en preview manual, focus trap funcional
- **Done**: tests TDD verdes, Nav refactorizado mobile-first, drawer accesible

### Tarea 3 (componentes UI bento/cards/timeline): refactor mobile-first

Paralelizable en 2-3 sub-tareas porque cada componente es independiente:

- **3a (heroes + section)**: `Hero.astro`, `HeroImpact.astro`, `SectionHeader.astro`
- **3b (cards + listas)**: `AwardCard.astro`, `ExperienceCard.astro`, `ExperienceTimeline.astro`, `ProjectCard.astro`, `ProjectBentoCard.astro`, `ProjectsBento.astro`, `CaseStudyExpander.astro`
- **3c (skills + stats + misc)**: `StatsBar.astro`, `SkillsGrid.astro`, `SkillsMarquee.astro`, `Footer.astro`, `ContactLinks.astro`, `NicheBadge.astro`

- **AC referenciados**: AC-1, AC-4, AC-5, AC-6
- **Depende de**: Tarea 1
- **Paralelizable con**: si entre 3a/3b/3c (no comparten archivo)
- **Verify por sub-tarea**: `pnpm run build` por app afectada + screenshot manual en 375px
- **Done**: cero scroll horizontal en 320px en cada componente

### Tarea 4 (app-shared + sections): refactor mobile-first

- **Archivos**: todos los `packages/app-shared/src/components/*.astro` + `packages/app-shared/src/pages/*.astro`
- **AC referenciados**: AC-1, AC-4, AC-5
- **Depende de**: Tarea 1, Tarea 3 (consumen heroes/cards refactorizados)
- **Paralelizable con**: ninguna interna (todos consumidos por SitePageLayout)
- **Verify**: `pnpm run build` exitoso en las 6 apps
- **Done**: paginas about + certificates renderizan sin overflow en 320px

### Tarea 5 (E2E verification): cv-screenshots multi-viewport

- **Archivos**: `tests/feature/smoke/cv-screenshots.spec.ts`
- **AC referenciados**: AC-10, AC-1, AC-5
- **Depende de**: Tareas 1-4 (necesita stack completo)
- **Paralelizable con**: ninguna (es la verificacion final)
- **Verify**: `python3 devtools/run.py docker up --env=local && python3 devtools/run.py test_runner --module=feature --type=feature --env=local` produce 54 screenshots
- **Done**: 54 screenshots commiteados o adjuntos, ninguno muestra overflow horizontal

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] Todos los AC numerados (AC-1 a AC-10) y mapeados a tests
- [ ] Tests TDD para `mobile-nav.ts` escritos y fallando (Red phase)
- [ ] `pnpm install` sin warnings nuevos
- [ ] `pnpm run dev` arranca limpio en las 6 apps
- [ ] No hay breaking changes en APIs publicas de `@portfolio/ui` (los
      componentes refactorizados mantienen sus props; solo se agregan
      `MobileNavDrawer` y `initMobileNav`)
- [ ] Plan revisado y aprobado por el usuario

### Definition of Done

- [ ] Todos los AC tienen al menos un test/screenshot que los cubre y pasa
- [ ] Coverage per-file >= 80% en `mobile-nav.ts` y archivos de `tests/`
- [ ] `pnpm exec tsc --noEmit` sin errores
- [ ] `pnpm exec astro check` sin errores en las 6 apps
- [ ] `pnpm exec biome check .` sin errores
- [ ] `pnpm run build` exitoso en todas las apps (output estatico en `dist/`)
- [ ] `pnpm run preview` verificado manualmente en 3 viewports (375, 768, 1280)
- [ ] Pre-commit + pre-push hooks pasan en local (`SKIP_STEPS=""`)
- [ ] `cv-screenshots.spec.ts` produce 54 screenshots sin overflow horizontal
- [ ] Documentacion actualizada: `.claude/rules/design-system.md` (agregar
      seccion de breakpoints), `.claude/rules/astro-landing.md` (mencionar
      mobile-first como convencion obligatoria)
- [ ] Commit conventional commits en espanol siguiendo `git-workflow.md`
- [ ] PR con body: Problema / Solucion / Como probar / TODO siguiendo
      `git-workflow.md`
