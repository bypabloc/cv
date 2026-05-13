# Carga de datos YAML en `@portfolio/content`

> Patron hibrido **TypeScript + YAML** para la data del CV. YAML = fuente
> (1 archivo por entry, slug-based filename). TypeScript = orquestador
> (glob + Zod + sort estable por slug).
>
> Esta rule explica QUE se hace, POR QUE, y COMO trabajar con ella.

## Activacion

Aplica cuando se trabaja con:

- Cualquier archivo bajo `packages/content/src/data/`
- Schemas Zod en `packages/content/src/schemas.ts`
- Configuracion de `vite-plugin-yaml` en Astro apps, Vitest o `cv-pdf`
- Errores tipo `Property 'glob' does not exist on type 'ImportMeta'`
- Errores tipo `loadYamlEntries: slug mismatch en ...`
- Errores Zod al parsear data (`expected YYYY-MM-DD`, etc.)

## Arquitectura del patron

```
packages/content/src/data/<entity>/
├── <slug-1>.yaml           # 1 archivo por entry
├── <slug-2>.yaml
├── ...
└── index.ts                # orquestador: glob + Zod + export
```

### index.ts (skeleton — 12 lineas)

```ts
import { loadYamlEntries } from '../../lib/load-yaml-entries'
import { type Entity, EntitySchema } from '../../schemas'

const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
  eager: true,
})

export const entries: readonly Entity[] = loadYamlEntries<Entity>(
  modules,
  EntitySchema,
)
```

### loadYamlEntries (helper)

Ubicacion: `packages/content/src/lib/load-yaml-entries.ts`.

Invariantes garantizadas:

1. **Slug-match enforced** — si el schema declara `slug: string`, el filename
   (`destacame-architect.yaml`) DEBE coincidir con el campo `slug` del YAML.
   Si no coinciden, lanza Error con ambos valores y el path absoluto.
2. **Sort estable por slug** — el array resultante esta ordenado
   ascendentemente por slug (independiente del orden de glob, que varia
   por OS/filesystem).
3. **Zod errors con path** — si el YAML rompe el schema, el Error incluye
   el path del archivo + mensaje Zod original.

## Configuracion del bundler

`import.meta.glob` + import de `.yaml` requieren TRES piezas configuradas
en CADA contexto que consuma `@portfolio/content`:

### 1. Plugin Vite (`@modyfi/vite-plugin-yaml`)

```ts
import yaml from '@modyfi/vite-plugin-yaml'
import { JSON_SCHEMA } from 'js-yaml'

export default defineConfig({
  plugins: [yaml({ schema: JSON_SCHEMA }), /* otros plugins */],
})
```

**JSON_SCHEMA es OBLIGATORIO**: bloquea la resolucion automatica de YAML 1.2
de strings tipo `2024-01-15` como `Date` object. Sin esto, Zod `DateSchema`
rechaza la entry (espera string).

### 2. Type ambient (`tsconfig.json`)

```jsonc
{
  "compilerOptions": {
    "types": [
      "vitest/globals",
      "vite/client",                         // para import.meta.glob
      "@modyfi/vite-plugin-yaml/modules"     // declare module '*.yaml'
    ]
  }
}
```

Ambos types son necesarios si el package importa YAML directa o
transitivamente (via `@portfolio/content`).

### 3. Devdeps del package

```bash
pnpm --filter <package> add -D @modyfi/vite-plugin-yaml js-yaml vite
```

`js-yaml` provee el `JSON_SCHEMA` constant. `vite` da los types de
`import.meta.glob`.

## Contextos donde se configura

| Contexto | Donde | Plugin |
|----------|-------|--------|
| App Astro (6 apps) | `apps/<app>/astro.config.ts` -> `vite.plugins` | si |
| Prebuild script (5 apps con CV) | `apps/<app>/scripts/vite.config.ts` + `package.json#scripts.prebuild` con `vite-node --config scripts/vite.config.ts` | si |
| `@portfolio/cv-pdf` CLI | `packages/cv-pdf/vite.config.ts` + script `vite-node` | si |
| Vitest del package `content` | `packages/content/vitest.config.ts` | si |
| Vitest de `app-shared` | `packages/app-shared/vitest.config.ts` | si |

Si un package nuevo importa `@portfolio/content`, hereda la obligacion.

## Agregar / modificar una entry

```bash
# Agregar una experiencia nueva
cat > packages/content/src/data/experiences/<slug>.yaml <<'EOF'
slug: <slug>            # debe matchear el filename
role:
  es: "<rol en es>"
  en: "<role in en>"
company: "<empresa>"
start: "2026-05"        # YYYY-MM
niches:                  # subset de [fintech, architect, leader, vibe, generic]
  - generic
priority:                # opcional, weights por niche
  generic: 50
responsibilities:
  es: ["..."]
  en: ["..."]
achievements:
  es: ["..."]
  en: ["..."]
skillsTechnical: ["..."]
skillsSoft: ["..."]
EOF

# Verificar
pnpm --filter @portfolio/content run typecheck
pnpm --filter @portfolio/content exec vitest run
```

Si el campo `slug` del YAML no matchea el filename, Vitest fallara en el
test de paridad con un mensaje claro.

## Errores frecuentes

### `Property 'glob' does not exist on type 'ImportMeta'`

Falta `"vite/client"` en `tsconfig.json#types`. Agregalo + asegura que
`vite` esta como devdep del package.

### `loadYamlEntries: el YAML "<path>" no expone default export`

El YAML no fue procesado por `vite-plugin-yaml`. Verifica:

1. Plugin esta en `vite.config.ts` / `astro.config.ts` / `vitest.config.ts`
2. Plugin esta ANTES de tailwindcss en el array (orden importa)
3. Estas corriendo `vite-node` (no `tsx`) si es un script CLI

### `loadYamlEntries: slug mismatch en <path>: filename="X" pero YAML.slug="Y"`

Renombra el archivo o ajusta el campo `slug` del YAML para que coincidan.
No hay forma de saltar este check (es invariante AC-3).

### Date parsed as `Date` object instead of string

Falta `schema: JSON_SCHEMA` en la config del plugin. js-yaml por default
resuelve `2024-01-15` como `Date`, lo que rompe Zod `DateSchema`.

### Errores al ejecutar prebuild

```
TypeError: (intermediate value).glob is not a function
```

El script esta corriendo con `tsx` en vez de `vite-node`. Cambia en
`package.json#scripts.prebuild`:

```diff
- "prebuild": "tsx scripts/build-public-assets.mjs"
+ "prebuild": "vite-node --config scripts/vite.config.ts scripts/build-public-assets.mjs"
```

## Anti-patterns

- Importar YAML directo con `import data from './foo.yaml'` — bypassa
  Zod. Usar siempre `loadYamlEntries`.
- Olvidar `JSON_SCHEMA` — fechas se parsean como Date, Zod falla en
  produccion pero no en typecheck.
- Re-introducir `data/<entity>.ts` con array inline — viola el patron
  y obliga a mantener 2 fuentes de verdad.
- Glob desde fuera del package (`import.meta.glob('packages/content/...')`
  en una app) — el glob es relativo al archivo que lo invoca y solo
  se resuelve cuando el index.ts del package esta DENTRO del scope
  del bundler que lo procesa.
