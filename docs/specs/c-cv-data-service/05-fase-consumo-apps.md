# 05 — Fase D: apps Astro consumen el API en prebuild

[<- 04 Fase C](04-fase-servicio-cv.md) | [Siguiente: archivos ->](06-archivos-afectados.md)

## Objetivo

Que las 6 apps Astro obtengan la data del CV del API `cv` en lugar de leer los
YAML de `packages/content/src/data/*`. La DB Neon pasa a ser fuente de verdad.

Depende de la Fase C deployada en `dev` y de la precondicion del seed.

## Estado actual del consumo

- Cada app tiene `scripts/build-public-assets.mjs` corrido en `prebuild` con
  `vite-node` (config en `scripts/vite.config.ts`).
- Las apps importan `@portfolio/content` (barrel `packages/content/src/index.ts`)
  que re-exporta `experiences`, `projects`, `profile`, etc. — arrays cargados
  de YAML con `loadYamlEntries` + Zod.
- Los componentes Astro consumen esos arrays con un shape validado por los Zod
  schemas de `packages/content/src/schemas.ts`.

## Estrategia: cliente API que preserva el shape

Para que el riesgo de migracion sea acotado, el cambio se concentra en UN
punto: el ORIGEN de la data. El shape que reciben los componentes NO cambia.

### `packages/content/src/lib/cv-api-client.ts` (NUEVO)

Cliente TypeScript que pega al API `cv` y valida la respuesta con los Zod
schemas YA existentes. Funciones que reflejan las del barrel actual:

```text
fetchCv(niche, locale)            -> CV completo
fetchExperiences(niche, locale)   -> Experience[]
fetchProjects(niche, locale)      -> Project[]
...una por coleccion
```

Cada funcion:
1. `fetch(API_BASE + '/cv?operation=cv&action=<x>&niche=<n>&locale=<l>')`.
2. Parsea el JSON.
3. Valida con el Zod schema correspondiente de `schemas.ts` (`ExperienceSchema`,
   etc.) — si el shape del API no matchea, falla ruidoso en build time.
4. Devuelve el array tipado, identico a lo que hoy devuelve el barrel.

`API_BASE` viene de una env var (`PUBLIC_CV_API_URL` o build-time):
`https://api.portfolio.dev.the-full-stack.com` en dev, etc. Mientras el API
Gateway no tenga custom domain, usar la URL `execute-api` resuelta de SSM.

### `packages/content/src/index.ts` (MODIFICAR)

Decision de transicion: el barrel puede exponer AMBOS — los arrays YAML
(deprecados) y las funciones `fetch*`. La fase D migra el `prebuild` de cada
app a las funciones `fetch*`; los YAML quedan como fallback hasta que un plan
posterior los elimine.

### `apps/<app>/scripts/build-public-assets.mjs` (MODIFICAR x6)

El prebuild pasa de:

```text
import { experiences, projects, ... } from '@portfolio/content'
```

a:

```text
import { fetchExperiences, fetchProjects, ... } from '@portfolio/content'
const experiences = await fetchExperiences(NICHE, LOCALE)
```

donde `NICHE` es el niche de la app (`fintech`, `architect`, ...; `generic`
para `generic` y `hub`).

### Resto de las apps (componentes / paginas)

Si los componentes importan `@portfolio/content` directamente (no solo en el
prebuild), evaluar por app. Idealmente la data ya viene resuelta del prebuild
como JSON estatico en `public/` o como prop — sin cambio en componentes. Esto
se confirma al explorar cada `build-public-assets.mjs` durante la ejecucion.

## Verificacion de la fase

```bash
# API cv deployado en dev primero
python devtools/run.py serverless deploy --lambda=cv --stage=dev --aws-profile=tfs-dev

# build de cada app consumiendo el API
pnpm --filter @portfolio/generic run build
pnpm --filter @portfolio/hub run build
pnpm --filter @portfolio/fintech run build
pnpm --filter @portfolio/architect run build
pnpm --filter @portfolio/leader run build
pnpm --filter @portfolio/vibe run build

# o todas:
pnpm run build
```

Criterio: las 6 apps buildean consumiendo el API; el `dist/` generado tiene
el mismo contenido del CV que con los YAML (AC-8). Comparar visualmente con
`pnpm run preview`.

## Done

- [ ] `cv-api-client.ts` creado, valida con los Zod schemas existentes
- [ ] barrel `index.ts` expone las funciones `fetch*`
- [ ] los 6 `build-public-assets.mjs` consumen el API
- [ ] `pnpm run build` de las 6 apps verde
- [ ] preview visual sin regresion vs los YAML

## TODO (fuera de scope de este plan)

- Eliminar `packages/content/src/data/*.yaml` y el barrel YAML una vez que el
  consumo via API este estable en prod. Es un plan de limpieza posterior.
- Custom domain del API Gateway (`api.portfolio.the-full-stack.com`) — ver
  skill `subdomain-standard`.

Continua en [06-archivos-afectados.md](06-archivos-afectados.md).
