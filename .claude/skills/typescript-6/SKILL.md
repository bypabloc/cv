---
name: typescript-6
description: >
  Reference for TypeScript 6.0 (GA march 23, 2026): breaking changes from 5.x,
  new features (native node.js .ts support, isolatedDeclarations, module Preserve,
  using/await using stable), strict mode obligatorio, module resolution defaults
  (ESNext + bundler), tsconfig canonicos para Astro 6 / Next.js 16 / packages
  compartidos del monorepo. Cubre verbatimModuleSyntax, noUncheckedIndexedAccess,
  project references, codemod ts5to6, Biome v2.3 + Biotype type-aware linting.
  Use when the user says "typescript 6", "ts 6", "tsconfig", "strict mode",
  "module resolution", "moduleResolution bundler", "verbatimModuleSyntax",
  "noUncheckedIndexedAccess", "isolatedDeclarations", "project references",
  "ts 5 to 6 migration", "ts5to6 codemod", "upgrade typescript",
  "typescript strict", "typescript performance", "import type",
  "typescript 6", "typescript 6.0", "tipos typescript", "configurar typescript",
  "actualizar typescript", "tsconfig estricto", "modo estricto", "tipos estrictos",
  "migracion typescript", "actualizar tsc", "typescript monorepo",
  "typescript breaking changes", "typescript pnpm workspace",
  "typescript next.js 16", "typescript astro 6", "typescript dashboard",
  "typescript portfolio".
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
argument-hint: "(opcional) tema especifico: strict, modules, tsconfig, migration, performance"
---

# TypeScript 6 — Skill de referencia

> TypeScript 6.0 GA (marzo 23, 2026) — ultima version JavaScript-based.
> TypeScript 7.0 (late 2026) sera reescrita en Go (10x mas rapida) y
> removera todos los deprecated flags. Preparar codigo en 6.0 hoy = upgrade
> a 7.0 sin friccion.
>
> Esta skill consolida el research de mayo 2026: breaking changes 5.x->6.0,
> features nuevos, tsconfig canonicos para los 3 contextos del repo (Astro 6,
> Next.js 16 dashboard, packages compartidos), patrones obligatorios y
> anti-patrones.

## Cuando usar esta skill

- Antes de tocar cualquier `tsconfig.json` o `tsconfig.base.json` del repo.
- Al diagnosticar errores de TypeScript en CI o pre-push hooks.
- Al planificar la migracion del repo de TS 5.x a 6.0.
- Al elegir entre `module` + `moduleResolution` para un package nuevo.
- Para revisar si un patron es idiomatico TS 6 o legacy TS 4/5.

## Knowledge tree

Detalle en `.claude/docs/typescript-6/`:

| Tema | Archivo |
|------|---------|
| Indice + reglas criticas | [README](../../docs/typescript-6/README.md) |
| Breaking changes 5.x -> 6.0 + codemod ts5to6 | [01-breaking-changes.md](../../docs/typescript-6/01-breaking-changes.md) |
| Features nuevos (native node .ts, isolatedDeclarations, using/await using) | [02-features.md](../../docs/typescript-6/02-features.md) |
| Strict mode + flags adicionales recomendados | [03-strict-mode.md](../../docs/typescript-6/03-strict-mode.md) |
| tsconfig canonicos por contexto (Astro / Next / package) | [04-tsconfig.md](../../docs/typescript-6/04-tsconfig.md) |

Rule de enforcement: [.claude/rules/typescript.md](../../rules/typescript.md).

## Resumen ejecutivo

### Versions

- TypeScript 6.0 GA: 23 marzo 2026 (ultima version JS-based)
- Patches 6.0.x: marzo-mayo 2026
- TypeScript 7.0 preview (Go port): finales de 2026

### Breaking changes que MAS impactan al portfolio

1. **`strict: true` ahora es default implicito** — codigo sin `strict` ve cientos de errores nuevos. Mitigacion: setear `"strict": false` TEMPORAL (deprecado en TS 7).
2. **`types` array OBLIGATORIO** — sin `"types": [...]` no se cargan `@types/*` globales. Cold builds 20-50% mas rapidos como contrapartida.
3. **`baseUrl` removed** — solo `paths` relativos. El codemod `ts5to6` lo resuelve auto.
4. **`module` default**: `commonjs` -> `ESNext`. **`moduleResolution` default**: `node` -> `bundler`.
5. **`target` minimo ES2015** (ES5 deprecated).
6. **`esModuleInterop` y `allowSyntheticDefaultImports` siempre `true`** — no se pueden setear `false`.
7. **`namespace Foo { }` reemplaza `module Foo { }`** (conflicto con propuesta ECMAScript de module blocks).

### Features nuevos clave

- **Native node.js `.ts` support** (Node 22.18+ / 23.6+): `node script.ts` sin compilar (type stripping).
- **`isolatedDeclarations`**: genera `.d.ts` sin full type-check (10x mas rapido para Bun/swc/tsup).
- **`module: "Preserve"`**: preserva imports exactos como fueron escritos.
- **`using` y `await using` stable** (Symbol.dispose / asyncDispose): cleanup automatico al salir scope.
- **Project references mejoradas**: `tsc -b` en paralelo, monorepos 22-package 11min -> 3min.

### Performance (TS 5.9 -> 6.0)

| Aspecto | Mejora |
|---------|--------|
| Cold build | -47% (15s -> 8s) |
| Incremental rebuild | -40 a -60% |
| Peak memory codebases grandes | -25% |
| Language service latency | -30% (200ms -> 140ms) |

## tsconfig canonicos para el portfolio

### Base compartida (`tsconfig.base.json` en root)

```jsonc
{
  "compilerOptions": {
    "target": "ES2023",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "verbatimModuleSyntax": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowJs": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "forceConsistentCasingInFileNames": true,
    "useDefineForClassFields": true
  },
  "exclude": ["node_modules", "dist", "build", ".astro", ".next"]
}
```

### App Astro 6 (`apps/<niche>/tsconfig.json`)

```jsonc
{
  "extends": ["astro/tsconfigs/strict", "../../tsconfig.base.json"],
  "compilerOptions": {
    "paths": { "@/*": ["./src/*"] },
    "types": ["astro/astro-jsx", "vitest/globals"]
  }
}
```

### Dashboard Next.js 16 (`dashboard/tsconfig.json`)

```jsonc
{
  "extends": ["@tsconfig/next", "../tsconfig.base.json"],
  "compilerOptions": {
    "jsx": "preserve",
    "incremental": true,
    "paths": { "@/*": ["./src/*"] },
    "types": ["node", "react", "react-dom", "vitest/globals"]
  },
  "include": ["src/**/*", ".next/types/**/*"]
}
```

### Package compartido (`packages/<X>/tsconfig.json`)

```jsonc
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "declarationMap": true,
    "composite": true,
    "incremental": true,
    "types": ["node", "vitest/globals"]
  },
  "include": ["src/**/*"],
  "exclude": ["dist", "node_modules", "tests"]
}
```

## Migracion 5.x -> 6.0 (receta corta)

```bash
# 1. Upgrade
pnpm add -D -w typescript@^6.0.0

# 2. Codemod (elimina baseUrl, ajusta paths, setea rootDir)
pnpm dlx @andrewbranch/ts5to6 .

# 3. Typecheck para ver errores nuevos
pnpm exec tsc --noEmit
pnpm exec astro check  # apps Astro

# 4. Listar @types en tsconfig.types (antes auto-discovered)
# 5. Arreglar strict errors (mayoria null checks)
# 6. Verificar builds
pnpm run build

# 7. Tests
pnpm exec vitest run --coverage
```

## Anti-patterns prohibidos en TS 6

| Anti-pattern | Por que | Alternativa |
|--------------|---------|------------|
| `any` | Bypassa type safety | `unknown` + narrow |
| `as Foo` casual | Bypassa type checker | `satisfies Foo` (preserva inference) |
| Olvidar `import type` | `verbatimModuleSyntax: true` lo detecta | Biome `useImportType` |
| `@types/X` sin listar en `types` | NO se carga en TS 6 | Listar en `tsconfig.types` |
| `module: "CommonJS"` con `moduleResolution: "bundler"` | Invalido en TS 6 | `module: "ESNext"` |
| `baseUrl` en tsconfig | Removed en TS 6 | Paths relativos |
| `module Foo { }` | Reemplazado por `namespace` | `namespace Foo { }` |
| Mutaciones en tipos React 19 | Incompatible React Compiler | Patrones inmutables |
| `target: "ES5"` | Deprecated | `target: "ES2023"` minimo |
| `ignoreDeprecations: "6.0"` permanente | NO funcionara en TS 7 | Arreglar deprecations ahora |

## Ecosystem mayo 2026

| Package | Version TS 6-ready |
|---------|-------------------|
| `@types/node` | 24.x |
| `@types/react` | 19.x |
| `astro` | 6.x |
| `next` | 16.x |
| `zod` | 4.x (`z.infer` stable) |
| `vitest` | 3.x |
| `biome` | 2.3+ (Biotype type-aware linting) |

## Comandos canonicos

```bash
# Typecheck local
pnpm exec tsc --noEmit
pnpm exec astro check                # apps Astro
pnpm --filter <app> typecheck        # via script

# Build con incremental
pnpm exec tsc -b                      # project references
pnpm exec tsc -b --watch              # watch mode
pnpm exec tsc -b --clean              # limpiar artifacts

# Codemod (una sola vez por migracion)
pnpm dlx @andrewbranch/ts5to6 .
```

## Referencias

- [Microsoft DevBlogs - Announcing TypeScript 6.0](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/)
- [Total TypeScript - tsconfig Cheat Sheet](https://www.totaltypescript.com/tsconfig-cheat-sheet)
- [TypeScript Handbook - Modules](https://www.typescriptlang.org/docs/handbook/modules/guides/choosing-compiler-options.html)
- Research raw (efimero): `tmp/research/typescript-6.md` (992 lineas)
