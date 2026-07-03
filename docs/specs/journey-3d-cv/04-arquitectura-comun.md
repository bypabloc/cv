# Arquitectura comun (todas las propuestas)

> [<- Extras](03-propuestas-extra.md) · [Siguiente: esfuerzo y Fable 5 ->](05-esfuerzo-y-fable5.md)

Cualquiera de las 6 propuestas se monta sobre la misma infraestructura. Esto
permite construir A primero y agregar B (o cambiar de escena) sin rehacer la
base. Cambiar de propuesta = cambiar la escena 3D, NO la infra.

## La app `apps/journey` (basada en `generic`)

- Nueva app en `apps/journey`, entra al pnpm workspace como `@portfolio/journey`.
- Se clona la estructura de `apps/generic` (que ya tiene el recorrido completo,
  React 18, `@astrojs/react`, Tailwind v4, el prebuild `fetch-cache`).
- Reusa TODOS los packages: `@portfolio/content` (datos), `@portfolio/ui`,
  `@portfolio/app-shared` (CvSections para el fallback), `@portfolio/seo`.
- Nueva dep: `three` + `@react-three/fiber` + `@react-three/drei` (+ `gsap`,
  `lenis`; `@react-three/rapier` solo si se hace la Propuesta G free-roam, o
  el character controller opcional de la Propuesta A habitaciones).

### Rutas

```
apps/journey/src/pages/
├── index.astro        # la experiencia 3D (Propuesta elegida) — client:only
├── en/index.astro     # i18n
└── cv.astro           # (opcional) el CV 2D canonico completo = fallback + SEO
```

> Decision abierta para el usuario: la experiencia 3D vive en `/` de la app
> journey (la app ES la experiencia), o en `/world` con `/` = CV 2D. Recomiendo
> `/` = 3D con degradado a 2D en el mismo componente (tier Static), y ademas
> exponer el CV 2D canonico para SEO/ATS.

## Isla WebGL (regla dura)

```astro
---
import Journey3D from '../components/Journey3D.tsx'
import CvSections from '@portfolio/app-shared/components/CvSections.astro'
---
<!-- fallback SEO/estatico SIEMPRE en el HTML (indexable) -->
<div id="cv-fallback"><CvSections ... /></div>
<!-- isla 3D: se monta solo en tier Full/Reduced, oculta el fallback -->
<Journey3D client:only="react" />
```

- **`client:only="react"`** obligatorio (NUNCA `client:load` -> rompe el build
  por `window`/`document` en el SSG).
- Toda la escena en UNA sola isla (el context de React no cruza islas; si hace
  falta estado compartido -> Zustand).
- **Dynamic import** del componente pesado dentro de la isla -> Vite/Rollup lo
  separa en su propio chunk, cargado bajo demanda. El CV texto NO descarga el
  bundle 3D.

## Datos (una fuente, dos vistas)

- Los hitos del mundo 3D se alimentan de `@portfolio/content` (mismo Zod + JSON
  cache que el CV 2D). Un solo dato -> vista 2D canonica + vista 3D.
- Prebuild: reusar el patron de `generic` (`fetch-cache` + build-public-assets)
  para generar un JSON de "hitos del journey" (posicion en el spline, bioma,
  elevacion por seniority) derivado de los 9 experiences + projects.
- Agregar un rol nuevo = agregar el YAML en la DB -> regenerar cache -> el
  sendero/mundo se recalcula. Data-driven, sin editar la escena a mano.

## Sistema de 3 tiers (fallback)

Detectado en el init de la isla, ANTES de montar la escena:

| Tier | Deteccion | Que recibe |
|------|-----------|-----------|
| **Full** | Desktop + WebGL2 + buena GPU (renderer string / mini-benchmark) | Escena 3D completa |
| **Reduced** | Movil con WebGL2, `deviceMemory` bajo | Escena simplificada: menos polys, sin post-processing, DPR capado, camara guiada por scroll |
| **Static** | `!WebGL` / HW debil / `prefers-reduced-motion` | NO monta la isla 3D -> el `#cv-fallback` (CvSections 2D) queda visible = storytelling legible + SEO/ATS |

- Feature-detection: `matchMedia('(prefers-reduced-motion)')` + check de WebGL2
  + `navigator.deviceMemory`. En tier Static NO se carga Three.js siquiera
  (ahorra el bundle y la bateria).
- drei `<AdaptiveDpr>` + `<PerformanceMonitor>` para bajar calidad dinamica
  dentro de Full/Reduced.

## Assets y Cloudflare

- Assets glTF/KTX2/Draco-decoder como estaticos en `public/` (o R2 si un
  archivo excede los **25 MiB** de Cloudflare Pages).
- Pipeline de build: `gltf-transform`/`gltfpack` aplica Draco (geometria) +
  KTX2/Basis (texturas) en batch antes de subir.
- Lazy-load por zona/escena (no cargar los 3 biomas de golpe -> crashea iOS por
  limite de contexto WebGL). drei `<Preload>` / `useGLTF.preload()` para
  prefetch selectivo de la siguiente zona.

## Deploy (Cloudflare Pages)

- Agregar `journey` a `APPS` en `devtools/cloudflare_setup/config.py`
  (`app_type='astro'`, `root_dir='apps/journey'`, `build_output_dir='dist'`).
- Subdominio segun el estandar: `journey.portfolio.dev.the-full-stack.com` (dev)
  y `journey.portfolio.the-full-stack.com` (prod). 2 Pages projects (uno por env).
- Correr `cloudflare_setup all --env=<X>` (projects + domains + dns) al crear.
- Agregar `journey` al matrix de `.github/workflows/deploy-apps.yml`.
- Env vars per env (client): las mismas que las otras apps (`PUBLIC_API_ENDPOINT`,
  `PUBLIC_TURNSTILE_SITEKEY`, `BASE_DOMAIN`) via `sync_secrets --category=client`.

> Si el usuario prefiere NO crear un subdominio nuevo: la experiencia puede
> vivir como ruta `/world` DENTRO de `apps/generic` (sin app nueva, sin Pages
> project extra). Trade-off: infla el repo de generic con el chunk 3D (aislado
> por dynamic import, pero comparte pipeline de build). El usuario pidio app
> nueva, asi que el plan default es `apps/journey`.

## Regla dura (repetida — es el ADN)

El 3D es una capa experiencial. El CV canonico 2D (indexable, ATS, GEO, PDF,
llms.txt, JSON-LD Person) sigue siendo la fuente de verdad. El WebGL NUNCA es
la unica via de leer el CV.
