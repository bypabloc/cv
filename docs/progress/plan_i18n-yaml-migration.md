# Plan: Migracion de textos de UI a YAML i18n

> Mover TODOS los textos de las 6 apps a archivos YAML, cargados en
> build-time, validados con Zod, separados en archivos de "elementos"
> (labels reutilizables) y de "curriculum" (textos del CV por app), cada
> uno asociado a una traduccion (es/en).

## 1. Contexto / Problema

Los textos de UI del portfolio estan hoy **hardcodeados en TypeScript**:

- `packages/app-shared/src/lib/site-config.ts` -> `buildStrings()` arma el
  objeto `I18nStrings` (meta, nav, hero, stats, sections, labels,
  atsKeywords) con strings es/en inline.
- Cada `apps/<app>/src/lib/site-config.ts` pasa overrides inline
  (hero, meta, atsKeywords) — 5 de 6 apps (hub no tiene).
- Componentes con texto hardcodeado adicional (~80 strings): `ContactForm`,
  `ContactFormReact.tsx`, `Footer`, `Nav`, `MobileNavDrawer`, `ThemeToggle`,
  `ContactLinks`, `CvSections` (filterLabels + mensajes de filtro vacio),
  `BaseLayout` (skip-link), `SitePageLayout` (schema nav + brand).

Los **datos del CV** (experiencias, proyectos, skills...) YA estan en YAML
en `packages/content/src/data/` via `loadYamlEntries` + Zod. La infra YAML
existe y funciona.

### Hallazgos de exploracion

- El proyecto ya tiene `vite-plugin-yaml` (JSON_SCHEMA), `loadYamlEntries`,
  validacion Zod y test de paridad por slug — se reutiliza todo.
- `loadYamlEntries` asume 1 entry por archivo en una carpeta + glob. Para
  i18n se necesita un loader nuevo: un solo YAML por idioma, no un glob de
  entries. No se fuerza `loadYamlEntries` a un caso que no es.
- Decisiones del usuario: base comun + override por app; YAML en
  `packages/content/src/data/i18n/`; 1 archivo por idioma; alcance =
  site-config + componentes + JS cliente; schema estricto + test paridad.

## 2. Solucion Propuesta

Crear un modulo i18n en `packages/content/src/data/i18n/` con DOS familias
de archivos YAML, cada una con 1 archivo por idioma, mas overrides por app.
Cargarlos en build-time, validarlos con Zod, y exponer un helper
`buildStrings()` que reemplaza el actual leyendo de YAML en vez de inline.

### Estructura de archivos

```text
packages/content/src/data/i18n/
├── elements/                       # labels reutilizables (genericos)
│   ├── elements.es.yaml            # nav, stats, sections, labels, ui de componentes
│   ├── elements.en.yaml
│   └── index.ts                    # loader + merge
├── curriculum/                     # textos del CV especificos por app
│   ├── _base.es.yaml               # defaults compartidos (hero, meta fallback)
│   ├── _base.en.yaml
│   ├── generic.es.yaml             # override de la app generic
│   ├── generic.en.yaml
│   ├── hub.es.yaml
│   ├── hub.en.yaml
│   ├── fintech.es.yaml … vibe.en.yaml   # 6 apps x 2 idiomas
│   └── index.ts                    # loader + merge base<-app
└── index.ts                        # barrel: re-exporta loaders + types
```

- **elements** = lo generico/reutilizable: items de nav, etiquetas de stats,
  titulos+subtitulos de secciones (Experiencia/Proyectos/Skills/...), labels
  (Descargar CV, Ver mas...) y los textos de componentes (form, footer, nav,
  theme toggle, cookie banner, contact links). Identico para las 6 apps.
- **curriculum** = lo especifico del CV de cada app: hero (eyebrow,
  headline, summary, nicheLabel), meta (title, description), atsKeywords,
  subtitulos de seccion overrideables. `_base.{lang}.yaml` lleva los
  defaults; `<app>.{lang}.yaml` solo las claves que difieren.

### Decisiones clave

- **Decision 1: dos familias de archivos (elements vs curriculum)** — el
  usuario pidio "los archivos de elementos y los archivos de curriculum
  deben estar separados". elements es estable y comun; curriculum cambia por
  app. Separarlos evita que un cambio de copy del hero de una app toque el
  archivo de labels compartidos.

- **Decision 2: 1 archivo por idioma (no claves multi-idioma)** — el usuario
  eligio este modelo. `elements.es.yaml` y `elements.en.yaml` tienen las
  mismas keys. Diffs limpios, agregar un idioma = agregar archivos. Coincide
  con el patron de `data/languages/`.

- **Decision 3: merge base + override por app para curriculum** — `_base`
  define todo; cada app solo redefine lo suyo. Replica el comportamiento
  actual de `SiteOverrides` (campos opcionales con `??` fallback) pero en
  datos, no en codigo.

- **Decision 4: loader propio `loadI18nFile`, no `loadYamlEntries`** —
  `loadYamlEntries` es para glob de N entries con slug-match. i18n es 1
  documento por idioma. Un loader nuevo (10-15 lineas) que hace
  `import` del YAML + `schema.parse` es mas honesto que forzar el glob.

- **Decision 5: `buildStrings` se mantiene como API, cambia su fuente** —
  `defineSiteConfig` y los `apps/<app>/src/lib/site-config.ts` siguen
  exportando `STRINGS`. Internamente `buildStrings` deja de tener strings
  inline y compone `elements + curriculum[app]`. Los componentes que reciben
  `strings`/`t` no cambian su interfaz.

- **Decision 6: JS de cliente recibe strings via data-attributes** — los
  componentes con `<script>` (ContactForm, ThemeToggle, ContactLinks)
  reciben los strings ya resueltos del lado servidor y los serializan en
  `data-*` o en un `<script type="application/json">`; el script de cliente
  los lee. Sin fetch en runtime: todo se resuelve en build.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given las 6 apps, When se hace `pnpm run build`, Then ningun
  texto visible de UI proviene de un string literal en `.astro`/`.ts`/`.tsx`
  — todo sale de un YAML de `data/i18n/`.
- **AC-2**: Given los archivos `elements.es.yaml` y `elements.en.yaml`,
  When un test compara sus claves, Then son exactamente identicas (paridad
  de traduccion); lo mismo para cada par `<app>.es.yaml`/`<app>.en.yaml`.
- **AC-3**: Given un YAML i18n que no cumple el schema Zod, When se carga,
  Then el build falla con un Error que incluye el path del archivo.
- **AC-4**: Given la app `vibe` con override de hero, When se renderiza,
  Then usa el hero de `curriculum/vibe.es.yaml` y los labels de seccion de
  `elements.es.yaml`, sin duplicar los labels en el archivo de vibe.
- **AC-5**: Given una clave presente en `_base` pero ausente en
  `<app>.yaml`, When se construye el curriculum de esa app, Then se usa el
  valor de `_base` (merge con fallback).
- **AC-6**: Given el form de contacto, When falla la validacion en el JS de
  cliente, Then el mensaje de error mostrado proviene del YAML i18n (no del
  string hardcodeado actual), en el idioma de la pagina.
- **AC-7**: Given los archivos de "elementos" y los de "curriculum", When se
  inspecciona el repo, Then estan en carpetas separadas y ningun archivo
  mezcla labels genericos con textos especificos del CV de una app.

## 4. Diagrama de Flujo (Antes y Despues)

### Antes

```text
apps/<app>/src/lib/site-config.ts  (overrides inline en TS)
        |
        v
defineSiteConfig() --> buildStrings()  [strings es/en HARDCODEADOS en TS]
        |
        v
   STRINGS  --> PageLayout / CvSections / componentes
                              ^
       componentes con texto HARDCODEADO propio (ContactForm, Footer...)
```

### Despues

```text
data/i18n/elements/*.yaml      data/i18n/curriculum/_base + <app>.yaml
        |                                   |
        v  loadElements(lang)               v  loadCurriculum(app, lang)
        +-----------------+-----------------+
                          v
              buildStrings()  [compone elements + curriculum, SIN inline]
                          v
                     STRINGS  --> PageLayout / CvSections / componentes
                          |
                          v  (strings de UI de cliente serializados)
              componentes leen su texto de `strings`/data-attrs (0 hardcode)
```

## 5. Diagrama ER

Aplica: se modelan entidades de content collection (schemas Zod nuevos).

```text
ElementsStrings (NUEVO)                CurriculumStrings (NUEVO)
- nav            array<NavItem>        - meta      object{title,description}
- stats          object               - hero      object{eyebrow,headline,
- sections       object{                          summary,nicheLabel,
    experience{title,subtitle},                   ctaPrimary,ctaSecondary}
    projects{title,subtitle}, ...}     - sections  object{ (*) subtitulos
- labels         object                            overrideables por app }
- components (*) object{               - atsKeywords  array<string>
    contactForm{...}, footer{...},
    nav{...}, themeToggle{...},
    cookieBanner{...}, contactLinks{...},
    filters{...} }

I18nStrings (resultado en runtime, NO cambia su shape publico)
  = ElementsStrings  ──  CurriculumStrings[app]   (merge 1-a-1)
```

Tipos validos: `string`, `array`, `object`, `boolean`.
`(*)` = campos nuevos respecto al `I18nStrings` actual (la rama
`components`). El resto del shape de `I18nStrings` se preserva para no
romper los componentes consumidores.

## 6. Tests Requeridos

### 6.B. Unit Tests (Vitest, en `packages/content/tests/`)

- `tests/data/i18n/elements.test.ts` — carga `elements.{es,en}.yaml`,
  valida que parsean con el schema [AC-3], y **paridad de claves** entre
  es/en [AC-2].
- `tests/data/i18n/curriculum.test.ts` — para cada app: carga
  `<app>.{es,en}.yaml`, valida schema [AC-3], paridad es/en [AC-2], y que
  el merge con `_base` rellena claves ausentes [AC-5].
- `tests/lib/build-strings.test.ts` — `buildStrings(app, lang)` produce un
  `I18nStrings` completo; la app `vibe` usa su hero y los labels base
  [AC-4]; claves de seccion sin override caen a `_base` [AC-5].
- Coverage v8 >= 80% per-file en los archivos nuevos.

### 6.C. Typecheck

- `pnpm exec tsc --noEmit` + `pnpm exec astro check` (recursive) sin
  errores: el tipo `I18nStrings` se deriva de los schemas Zod
  (`z.infer`), los componentes consumidores deben seguir tipando.

### 6.D. E2E Tests

N/A en este plan — la migracion es interna (texto sale del mismo lugar
visual). Verificacion visual via `pnpm run preview` cubre regresiones de
copy. Si el pre-push hook corre Playwright, sirve de red de seguridad pero
no se agregan specs nuevas.

## 7. Archivos Afectados

### Crear

- `packages/content/src/data/i18n/elements/elements.es.yaml` — labels
  genericos en espanol (nav, stats, sections, labels, components)
- `packages/content/src/data/i18n/elements/elements.en.yaml` — idem ingles
- `packages/content/src/data/i18n/elements/index.ts` — `loadElements(lang)`
- `packages/content/src/data/i18n/curriculum/_base.es.yaml` — defaults CV es
- `packages/content/src/data/i18n/curriculum/_base.en.yaml` — defaults CV en
- `packages/content/src/data/i18n/curriculum/{generic,hub,fintech,architect,leader,vibe}.{es,en}.yaml`
  — 12 archivos, override de hero/meta/atsKeywords por app
- `packages/content/src/data/i18n/curriculum/index.ts` —
  `loadCurriculum(app, lang)` con merge `_base` <- `<app>`
- `packages/content/src/data/i18n/index.ts` — barrel del modulo i18n
- `packages/content/src/lib/load-i18n-file.ts` — loader generico de 1 YAML
  + Zod (no glob)
- `packages/content/tests/data/i18n/elements.test.ts`
- `packages/content/tests/data/i18n/curriculum.test.ts`
- `packages/content/tests/lib/build-strings.test.ts`
  - Verificar (los 4): `pnpm --filter @portfolio/content exec vitest run`

### Modificar

- `packages/content/src/schemas.ts` — agregar `ElementsStringsSchema`,
  `CurriculumStringsSchema` + tipos inferidos `ElementsStrings`,
  `CurriculumStrings`
  - Verificar: `pnpm --filter @portfolio/content run typecheck`
- `packages/content/src/index.ts` — re-exportar loaders i18n + tipos
- `packages/content/vitest.config.ts` — confirmar que el plugin YAML cubre
  el glob nuevo (probablemente ya, es `*.yaml`)
- `packages/app-shared/src/lib/site-config.ts` — `buildStrings()` deja de
  tener strings inline; compone `loadElements` + `loadCurriculum`. El tipo
  `I18nStrings` pasa a derivar de los schemas Zod. `SiteOverrides` se
  reduce o elimina (los overrides viven en YAML).
  - Verificar: `pnpm --filter @portfolio/app-shared run typecheck`
- `packages/app-shared/src/lib/define-site-config.ts` — `defineSiteConfig`
  recibe solo `niche` + `siteUrl` (ya no `overrides` inline); resuelve
  STRINGS desde el YAML del niche
  - Verificar: `pnpm --filter @portfolio/app-shared exec vitest run`
- `apps/{generic,fintech,architect,leader,vibe}/src/lib/site-config.ts` —
  eliminar el bloque `overrides` inline (migrado a YAML); quedan ~8 lineas
- `apps/hub/src/lib/site-config.ts` — idem (si existe; hub hoy no tiene
  archivo propio — verificar y crear/ajustar segun corresponda)
  - Verificar (las 6 apps): `pnpm run build`
- `packages/ui/src/components/ContactForm.astro` — recibe `strings` del
  form via prop; los ~40 textos (labels, placeholders, mensajes de
  validacion y de status) salen de YAML; el `<script>` lee los strings de
  un `data-*`/JSON inline
- `packages/ui/src/components/ContactFormReact.tsx` — idem via props
- `packages/ui/src/components/Footer.astro` — copyright, rights, manage
  consent desde YAML
- `packages/ui/src/components/Nav.astro` — locale switch label, aria menu
- `packages/ui/src/components/MobileNavDrawer.astro` — close/menu labels
- `packages/ui/src/components/ThemeToggle.astro` — aria-labels (server +
  fallback de JS via data-attrs)
- `packages/ui/src/components/ContactLinks.astro` — labels copy/copied/error
- `packages/ui/src/components/CookieBanner.astro` — reemplazar
  `getBannerCopy()` por strings del YAML
- `packages/ui/src/layouts/BaseLayout.astro` — "Skip to content"
- `packages/app-shared/src/layouts/SitePageLayout.astro` — schema nav items
  + brand name desde YAML/profile
- `packages/app-shared/src/components/CvSections.astro` — `filterLabels` y
  los mensajes "No hay experiencias/proyectos con estos filtros" salen de
  `strings`
  - Verificar (componentes): `pnpm exec astro check` + `pnpm run build` +
    `pnpm run preview` (revision visual de las 6 apps)

### Eliminar

- Los bloques de strings inline dentro de `buildStrings()` y de cada
  `overrides:` de app (se eliminan como parte de "Modificar", no son
  archivos completos).

## 8. Descomposicion para Paralelizacion

N/A — el plan es Medium (no llega a 11+ archivos de logica independiente;
los 12 YAML de curriculum son datos, no codigo). Se implementa secuencial:
schemas -> loaders -> YAML -> refactor site-config -> componentes -> tests.

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] AC-1..AC-7 numerados y referenciados por tests
- [ ] Tests de paridad y de loaders escritos y fallando (Red)
- [ ] `pnpm install` sin warnings; `vite-plugin-yaml` ya presente
- [ ] `pnpm run dev` arranca limpio antes de empezar

### Definition of Done

- [ ] Todos los AC tienen al menos un test que los cubre y pasa
- [ ] Coverage per-file >= 80% en archivos nuevos de `packages/content`
- [ ] `pnpm exec tsc --noEmit` + `pnpm exec astro check` sin errores
- [ ] `pnpm exec biome check .` sin errores
- [ ] `pnpm run build` exitoso en las 6 apps
- [ ] `pnpm run preview` verificado visualmente: el copy de las 6 apps se
      ve identico al actual (sin regresiones de texto)
- [ ] Grep de control: 0 strings de UI visibles hardcodeados en los
      componentes migrados
- [ ] Pre-commit hooks pasan en local
