# TypeScript 6 Standards

> Reglas duras de TypeScript 6 (GA marzo 23, 2026) para el portfolio: strict
> mode obligatorio, `module: ESNext` + `moduleResolution: bundler` para los
> 6 apps Astro y el dashboard Next.js, `verbatimModuleSyntax`, `types` array
> explicito, sin `baseUrl`. Pensado para el monorepo pnpm con 6 apps + 5
> packages compartidos.
>
> El detalle (breaking changes, features nuevos, tsconfig canonicos,
> migracion) vive en la skill `typescript-6` y en
> `.claude/docs/typescript-6/`. Esta rule es la enforcement con
> SIEMPRE/NUNCA.

## Activacion

Aplica SIEMPRE que se trabaje con:

- Cualquier archivo `.ts` o `.tsx` del repo (incluye `.astro` con `<script>`).
- Cualquier `tsconfig.json` (root, apps, packages).
- `package.json` cuando cambia la dep `typescript` o `@tsconfig/*`.
- Decidir entre `module`/`moduleResolution` para un workspace nuevo.
- Resolver errores `tsc --noEmit` o `astro check` antes de commit/push.

NO aplica al codigo Python de `devtools/` ni al codigo TypeScript de Lambdas
(que estan en otro repo). Las Lambdas son Python 3.13.

## Reglas duras (SIEMPRE / NUNCA)

### TypeScript-only en codigo de aplicacion (POLITICA RAIZ)

- **SIEMPRE TypeScript** — todo codigo de aplicacion del repo se escribe
  en `.ts`, `.tsx` o como bloque `<script lang="ts">` / frontmatter TS
  dentro de `.astro`. JavaScript nativo (`.js`, `.jsx`, `.mjs`, `.cjs`)
  esta **PROHIBIDO** en codigo de aplicacion.
- **SIEMPRE typing explicito** — toda funcion publica, parametro y campo
  publico declara su tipo. La inferencia esta bien para variables locales
  obvias; en interfaces publicas el tipo es explicito.
- **NUNCA** `any` — bajo ninguna circunstancia, ni en codigo de
  aplicacion, ni en tests, ni en mocks, ni en utilities. Si necesitas
  escape del type checker, usar `unknown` + narrow (type guard o
  `typeof`/`instanceof`), o `satisfies` para preservar inference, o un
  schema runtime (Zod) que produce el tipo via `z.infer`.
- **NUNCA** `.js` / `.jsx` / `.mjs` / `.cjs` en `src/`, `apps/<X>/src/`,
  `packages/<X>/src/`, `dashboard/src/`, `tests/` ni en cualquier carpeta
  de codigo de aplicacion.
- **NUNCA** `@ts-ignore` permanente — usar `@ts-expect-error` con un
  comentario explicando el motivo Y ticket/issue para resolverlo, o
  arreglar el root cause.

#### Excepciones (acotadas y documentadas)

Solo se permite JavaScript nativo en estos casos puntuales:

1. **Configs de root** que un toolchain requiere explicitamente como JS:
   `astro.config.mjs` (si la version Astro lo exige), `postcss.config.mjs`,
   `next.config.mjs` (si Next no aceptara `.ts`). Cuando el toolchain
   acepta `.ts`, usar siempre `.ts` (ej. `astro.config.ts`,
   `next.config.ts`).
2. **Archivos generados por terceros** (codemod output, snapshots, etc.)
   que viven en su carpeta de output y no se editan a mano.
3. **Hooks Python o scripts shell** — quedan fuera del scope de esta rule
   (son otros lenguajes).

Toda excepcion es un archivo concreto, documentado por ubicacion. NO se
acepta "tengo prisa, lo subo como .js y luego lo paso".

### Configuracion del compiler

- **SIEMPRE** `"strict": true` en todo tsconfig.json (root y apps). Cubre
  `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`,
  `strictBindCallApply`, `strictPropertyInitialization`, `noImplicitThis`,
  `alwaysStrict`, `useUnknownInCatchVariables`.
- **SIEMPRE** `"noUncheckedIndexedAccess": true` (previene `undefined` en
  acceso por indice — critico para arrays/dicts).
- **SIEMPRE** `"verbatimModuleSyntax": true` (obliga `import type` para
  imports type-only). Biome enforza con `useImportType`.
- **SIEMPRE** `"module": "ESNext"` + `"moduleResolution": "bundler"` para
  apps Astro y el dashboard Next.js (los bundlers Vite/Turbopack lo esperan).
- **SIEMPRE** listar `@types/*` en `"types": [...]`. En TS 6 NO hay
  auto-discovery — sin `types` no se cargan tipos globales.
- **SIEMPRE** `"target": "ES2023"` minimo (ES5 esta deprecado en TS 6).
- **SIEMPRE** `"skipLibCheck": true` (acelera builds; los `@types` confiamos
  que estan bien tipados).
- **SIEMPRE** `"isolatedModules": true` (compatible con esbuild/swc/Turbopack).
- **SIEMPRE** `"forceConsistentCasingInFileNames": true` (catch bugs en
  filesystems case-insensitive).
- **NUNCA** `"baseUrl"` — REMOVIDO en TS 6. Usar paths relativos en `"paths"`.
- **NUNCA** `"module": "CommonJS"` con `"moduleResolution": "bundler"` —
  combinacion invalida en TS 6.
- **NUNCA** `"target": "ES5"` — deprecated, error en TS 6.
- **NUNCA** `"esModuleInterop": false` ni `"allowSyntheticDefaultImports": false` —
  removidos, ambos siempre `true` en TS 6.
- **NUNCA** `"ignoreDeprecations": "6.0"` permanente — NO funcionara en TS 7.
  Solo como mitigacion temporal durante migracion.

### Sintaxis del codigo

- **SIEMPRE** `import type { X } from 'pkg'` para imports type-only
  (enforced por `verbatimModuleSyntax`).
- **SIEMPRE** `unknown` en vez de `any`. Si necesitas escape, narrow con
  type guard (`if (typeof x === 'string')`) o `satisfies`.
- **SIEMPRE** `satisfies Foo` en vez de `as Foo` para validar contra tipo
  sin perder literal inference.
- **SIEMPRE** `namespace Foo { }` en vez de `module Foo { }` (este ultimo
  es ERROR en TS 6 por conflicto con propuesta ECMAScript de module blocks).
- **SIEMPRE** `using` / `await using` para resources con `Symbol.dispose`
  / `Symbol.asyncDispose` (cleanup automatico).
- **NUNCA** `any` (excepto en cast deliberado documentado con `// reason: X`).
- **NUNCA** `as` cast sin razon explicita — bypassa el type checker.
- **NUNCA** `module Foo { }` syntax.
- **NUNCA** `Object.keys(obj)` sin cast — retorna `string[]`, no `keyof T`.
  Usar `Object.keys(obj) as (keyof typeof obj)[]` cuando sea seguro.

### Workspace y packages

- **SIEMPRE** los packages compartidos (`packages/<X>/`) extienden de
  `tsconfig.base.json` del root.
- **SIEMPRE** los packages que se consumen entre si declaran `"composite": true`
  + `"references": [...]` apuntando a los packages dependencia (project
  references — TS 6 paraleliza `tsc -b`).
- **SIEMPRE** los packages publicables (`@portfolio/content`, `@portfolio/ui`,
  etc.) tienen `"declaration": true` + `"declarationMap": true` (genera
  `.d.ts` consumibles).
- **SIEMPRE** considerar `"isolatedDeclarations": true` para packages
  internos (genera `.d.ts` sin invocar full type-checker, ~10x mas rapido).
  Trade-off: obliga tipos explicitos en exports publicos.
- **NUNCA** cross-import entre packages sin pasar por su `index.ts` (el
  barrel re-exporta lo publico; los `internal/` quedan privados).

### Performance

- **SIEMPRE** `"incremental": true` en apps y packages para builds rapidos.
  Genera `.tsbuildinfo` (gitignored).
- **SIEMPRE** correr `tsc -b` (build mode) para project references — paraleliza.

## tsconfig canonicos (referencia rapida)

Plantillas completas en
[.claude/docs/typescript-6/04-tsconfig.md](../docs/typescript-6/04-tsconfig.md).
Resumen:

| Contexto | Extends | Key settings |
|----------|---------|--------------|
| Root (`tsconfig.base.json`) | — | strict + verbatimModuleSyntax + bundler |
| App Astro (`apps/<X>/tsconfig.json`) | `astro/tsconfigs/strict` + base | `paths`, `types: ['astro/astro-jsx', 'vitest/globals']` |
| Dashboard Next.js (`dashboard/tsconfig.json`) | `@tsconfig/next` + base | `jsx: 'preserve'`, `incremental`, types React |
| Package (`packages/<X>/tsconfig.json`) | base | `composite`, `declaration`, `outDir: './dist'` |

## Migracion 5.x -> 6.0 (cuando aplique)

```bash
# 1. Upgrade typescript en root del workspace
pnpm add -D -w typescript@^6.0.0

# 2. Codemod oficial (Andrew Branch, TS team)
pnpm dlx @andrewbranch/ts5to6 .
# Elimina baseUrl, ajusta paths, setea rootDir, sigue extends chains

# 3. Typecheck para ver errores nuevos (mayoria null checks)
pnpm exec tsc --noEmit
pnpm exec astro check  # apps Astro

# 4. Listar @types/* en tsconfig "types" (antes auto-discovered)

# 5. Arreglar errores strict
# 6. Verificar builds + tests
pnpm run build
pnpm exec vitest run --coverage
```

## Verificacion (antes de declarar listo)

```bash
# Typecheck global
pnpm run typecheck
# o por workspace
pnpm --filter <app-o-package> typecheck

# Para apps Astro
pnpm --filter <app> exec astro check

# Build (detecta errores que typecheck no ve)
pnpm --filter <app> run build

# Tests
pnpm exec vitest run --coverage
```

## Anti-patterns

| Anti-pattern | Por que | Correccion |
|--------------|---------|------------|
| `any` en cualquier lugar | Bypassa type safety, oculta bugs | `unknown` + narrow / type guard |
| `as Foo` sin razon | Bypassa type checker | `satisfies Foo` (preserva inference) |
| Olvidar `import type` para tipos | `verbatimModuleSyntax` enforza, build falla | Biome `useImportType` auto-fix |
| `@types/X` no listado en `types` | NO se carga en TS 6, intellisense roto | Agregar a `tsconfig.types` |
| `baseUrl` en tsconfig nuevo | REMOVIDO en TS 6 | Solo `paths` relativos |
| `module: "CommonJS"` en app frontend | Invalido con `moduleResolution: "bundler"` | `module: "ESNext"` |
| `module Foo { }` legacy | ERROR en TS 6 | `namespace Foo { }` |
| `Object.keys(obj)` sin cast | Retorna `string[]`, perdes type info | `as (keyof typeof obj)[]` |
| Catch sin `unknown` | TS 6 fuerza `useUnknownInCatchVariables` | `catch (e: unknown) { if (e instanceof Error) ... }` |
| `ignoreDeprecations: "6.0"` como solucion final | Falla en TS 7 | Arreglar el deprecation now |
| Re-exportar tipos sin `export type` | `verbatimModuleSyntax` enforza | `export type { Foo }` |
| Hardcodear ruta a `node_modules/@types/...` | Brittle | `types: [...]` en tsconfig |

## Cuando esta rule SI aplica

Cualquier cambio a:

1. Archivos `*.ts` / `*.tsx` en `apps/`, `packages/`, `dashboard/`, `tests/`.
2. Bloques `<script lang="ts">` o frontmatter TS en `*.astro`.
3. Configuraciones: `tsconfig.json`, `tsconfig.base.json`, `tsconfig.*.json`.
4. Dependency upgrade de `typescript` o `@tsconfig/*`.
5. Creacion de un workspace nuevo (definir su `tsconfig.json` desde cero).

## Cuando NO aplica

- Codigo Python (`devtools/`, `.git-hooks/`) — usar rule `python.md`.
- Codigo Lambda (en otro repo) — ese repo tiene su propio standard Python.
- Archivos JSON / YAML puros — no involucran TypeScript.
- Documentacion `.md` — sin tipos.

## Referencias

- Skill: [`typescript-6`](../skills/typescript-6/SKILL.md)
- Docs (knowledge tree): [.claude/docs/typescript-6/](../docs/typescript-6/)
- Rule del dashboard (consume TS 6): [.claude/rules/dashboard.md](dashboard.md)
- Rule de Astro (consume TS 6): [.claude/rules/astro-landing.md](astro-landing.md)
- Research raw (efimero): `tmp/research/typescript-6.md`
