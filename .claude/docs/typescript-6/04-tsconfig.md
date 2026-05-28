# 04 — tsconfig.json Canonicos

[< 03-strict-mode](03-strict-mode.md) | [Volver al README](README.md)

> Plantillas concretas para los 3 contextos del portfolio: base
> compartida del root, apps Astro 6, dashboard Next.js 16, packages
> compartidos.

## Base compartida (`tsconfig.base.json` en root)

```jsonc
{
  "compilerOptions": {
    // Lenguaje y libs
    "target": "ES2023",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],

    // Module system
    "module": "ESNext",
    "moduleResolution": "bundler",

    // Strict (cubre 8 flags) + extras
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "verbatimModuleSyntax": true,
    "noFallthroughSwitchClause": true,

    // Interop
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowJs": true,
    "resolveJsonModule": true,
    "isolatedModules": true,

    // Quality of life
    "forceConsistentCasingInFileNames": true,
    "useDefineForClassFields": true
  },
  "exclude": ["node_modules", "dist", "build", ".astro", ".next", "out"]
}
```

## App Astro 6 (`apps/<niche>/tsconfig.json`)

```jsonc
{
  "extends": ["astro/tsconfigs/strict", "../../tsconfig.base.json"],
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    },
    "jsx": "preserve",
    "types": ["astro/astro-jsx", "vitest/globals", "@modyfi/vite-plugin-yaml/modules"]
  },
  "include": ["src/**/*", "tests/**/*"],
  "exclude": ["node_modules", "dist", ".astro"]
}
```

> Nota: `astro/tsconfigs/strict` ya setea `allowJs: false` y otros — el
> extends en orden mezcla y el segundo gana donde hay overlap. El portfolio
> mantiene la rule estricta de "no JS nativo" — ver
> [.claude/rules/typescript.md](../../rules/typescript.md).

## Dashboard Next.js 16 (`dashboard/tsconfig.json`)

```jsonc
{
  "extends": ["@tsconfig/next", "../tsconfig.base.json"],
  "compilerOptions": {
    "target": "ES2023",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],

    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "verbatimModuleSyntax": true,

    "jsx": "preserve",
    "incremental": true,
    "paths": {
      "@/*": ["./src/*"]
    },
    "types": ["node", "react", "react-dom", "vitest/globals"],

    "plugins": [{ "name": "next" }]
  },
  "include": ["src/**/*", ".next/types/**/*", "tests/**/*"],
  "exclude": ["node_modules", ".next", "build", "out"]
}
```

## Package compartido (`packages/<X>/tsconfig.json`)

```jsonc
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src",

    // Declaracion de tipos publicos
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,

    // Project references (paraleliza build entre packages)
    "composite": true,
    "incremental": true,

    // isolatedDeclarations acelera build (10x) pero exige tipos explicitos
    // en exports publicos. Activar package-por-package cuando este listo.
    // "isolatedDeclarations": true,

    "types": ["node", "vitest/globals"]
  },
  "include": ["src/**/*"],
  "exclude": ["dist", "node_modules", "tests"],
  "references": [
    // Si depende de otros packages, listar aqui:
    // { "path": "../content" }
  ]
}
```

## Root del monorepo (`tsconfig.json`) — solo project references

```jsonc
{
  "files": [],
  "references": [
    { "path": "packages/content" },
    { "path": "packages/ui" },
    { "path": "packages/seo" },
    { "path": "packages/cv-pdf" },
    { "path": "packages/app-shared" }
  ]
}
```

Build paralelo con `pnpm exec tsc -b`.

## Vitest config (`vitest.config.ts` por workspace)

Vitest hereda tsconfig automaticamente. Si necesitas override:

```typescript
import { defineConfig } from 'vitest/config'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [tsconfigPaths()],
  test: {
    environment: 'happy-dom',
    coverage: {
      provider: 'v8',
      thresholds: { perFile: { lines: 80, statements: 80, functions: 80, branches: 80 } }
    }
  }
})
```

## Verificacion

```bash
# Typecheck por workspace
pnpm --filter @portfolio/<X> typecheck

# Astro check (apps)
pnpm --filter @portfolio/<app> exec astro check

# Build con project references
pnpm exec tsc -b

# Build con watch (dev local)
pnpm exec tsc -b --watch

# Limpiar artifacts
pnpm exec tsc -b --clean
```

## Migracion desde tsconfig actual

Si el `tsconfig.json` actual tiene `baseUrl` o `module: "CommonJS"`:

```bash
pnpm dlx @andrewbranch/ts5to6 .
```

El codemod actualiza todos los tsconfig del monorepo recursivamente
(sigue extends chains).

## Decision: `astro/tsconfigs/strict` vs base custom

Astro provee 3 presets: `base`, `strict`, `strictest`. Usar `strict`
(no `strictest` — activa `noUncheckedIndexedAccess` + otras pero el
portfolio ya las setea desde su base custom).

El extends en orden:

```jsonc
{ "extends": ["astro/tsconfigs/strict", "../../tsconfig.base.json"] }
```

El segundo (`../../tsconfig.base.json`) gana donde hay overlap (precedencia
del ultimo). Asi el portfolio mantiene `noUncheckedIndexedAccess` +
`verbatimModuleSyntax` aun si el preset Astro no los activa.
