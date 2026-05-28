---
description: "Estandares Astro 6 + TypeScript 6 + Biome v2 para el portfolio (raiz del repo)."
globs: "src/**,public/**,tests/**,astro.config.*,biome.json,tsconfig.json,vitest.config.*,package.json"
---

# Astro Portfolio - Estandares de Desarrollo

> Reglas para el portfolio/CV personal en la raiz del repo: Astro 6 + TypeScript 6 + Biome v2.
> Output estatico. Sin backend, sin DB, sin auth.
>
> Design System (soporte dark y light) en `.claude/rules/design-system.md`.

## Stack

- Astro 6 (`output: 'static'` por defecto, sin SSR)
- TypeScript 6 strict
- Biome v2 (linter + formatter unificado)
- Vitest + happy-dom (unit tests)
- Playwright (E2E opcional, on-demand)
- pnpm como package manager
- Tailwind v4 (opcional, via `@tailwindcss/vite`) si se decide usar utility classes
- Fonts self-hosted via `@fontsource/*` (NUNCA Google Fonts CDN)

## Estructura

```text
.
├── src/
│   ├── pages/              # Rutas Astro
│   │   ├── index.astro     # Home (perfil + hero)
│   │   ├── about.astro     # Sobre mi (opcional)
│   │   ├── experience.astro
│   │   ├── projects.astro
│   │   └── contact.astro
│   ├── layouts/            # Layouts Astro
│   │   └── BaseLayout.astro
│   ├── components/         # Componentes reutilizables
│   │   ├── Hero.astro
│   │   ├── ExperienceCard.astro
│   │   ├── ProjectCard.astro
│   │   └── ThemeToggle.astro
│   ├── content/            # Content collections (opcional)
│   │   ├── config.ts       # schemas Zod
│   │   ├── experience/
│   │   ├── projects/
│   │   └── education/
│   ├── lib/                # Utilities
│   │   ├── format-date.ts
│   │   └── validators/
│   ├── styles/
│   │   ├── tokens.css      # CSS vars del DS
│   │   ├── typography.css
│   │   ├── fonts.css       # @fontsource imports
│   │   └── global.css
│   └── env.d.ts
├── public/                 # Assets estaticos (favicon, og-image, CV.pdf)
├── tests/
│   ├── unit/               # Vitest, mirror de src/
│   └── e2e/                # Playwright (opcional)
├── astro.config.ts
├── biome.json
├── tsconfig.json
├── vitest.config.ts
├── package.json
├── pnpm-lock.yaml
└── .nvmrc
```

## Componentes Astro

- Archivos `.astro` (frontmatter + template HTML/JSX-like)
- Frontmatter: codigo TypeScript dentro de `---`
- Template: HTML/JSX con sintaxis especifica de Astro (`{...}` para expresiones)
- Naming: PascalCase (`Hero.astro`, `ExperienceCard.astro`)
- Co-localizar por dominio cuando aplique (`components/cv/`, `components/projects/`)
- Props tipadas via interface `Props` exportada en el frontmatter

```astro
---
/**
 * @component ExperienceCard
 * @description Tarjeta de experiencia laboral del CV
 * @props {string} role - Cargo (ej. "Senior Frontend")
 * @props {string} company - Empresa
 * @props {string} startDate - YYYY-MM
 * @props {string} [endDate] - YYYY-MM, omitir para "Presente"
 */
interface Props {
  role: string
  company: string
  startDate: string
  endDate?: string
}
const { role, company, startDate, endDate } = Astro.props
---

<article class="experience-card">
  <h3>{role}</h3>
  <p class="company">{company}</p>
  <p class="dates">{startDate} — {endDate ?? 'Presente'}</p>
  <slot />
</article>
```

## Conformance (Biome v2 strict)

- Biome v2 como linter y formatter unificado.
- Config: `biome.json` en raiz (estricto, sin overrides salvo tests/configs).
- Ejecutar: `pnpm exec biome check .`
- Auto-fix: `pnpm exec biome check --write .`

### Reglas activas recomendadas (errores que bloquean el commit)

**complexity**: `noExcessiveCognitiveComplexity` (max 15), `noUselessFragments`, `noUselessTernary`, `useArrowFunction`, `useFlatMap`, `useSimpleNumberKeys`, `useLiteralKeys`, `useNumericLiterals`.

**correctness**: `noUnusedVariables`, `noUnusedImports`, `noUnusedFunctionParameters` (warn), `noUnusedPrivateClassMembers`, `noConstantMathMinMaxClamp`, `noSelfAssign`.

**style**: `useImportType`, `useExportType`, `useConst`, `useTemplate`, `noUselessElse`, `useShorthandAssign`, `useShorthandFunctionType`, `useDefaultParameterLast`, `useExponentiationOperator`, `useSelfClosingElements`, `useSingleVarDeclarator`, `noNonNullAssertion` (warn), `noParameterAssign`, `noYodaExpression`, `useCollapsedElseIf`, `useConsistentArrayType` (`T[]`).

**suspicious**: `noExplicitAny`, `noConsole` (allow=`warn`,`error`,`info`), `noDoubleEquals`, `noEmptyBlockStatements`, `noShadowRestrictedNames`, `noFallthroughSwitchClause`, `noMisleadingCharacterClass`, `noVar`, `useDefaultSwitchClauseLast`.

**nursery**: `noFloatingPromises` (error), `noShadow` (warn).

**performance**: `noAccumulatingSpread`, `noDelete`.

**security**: `noDangerouslySetInnerHtml` (XSS), `noGlobalEval`.

### Overrides por contexto

| Path | Reglas relajadas |
|------|------------------|
| `tests/e2e/**` | complexity, console, unused, floating-promises, non-null OFF |
| `tests/unit/**` | complexity, console, empty-blocks, non-null OFF |
| `*.astro` | `noUnusedImports/Variables` OFF, `useImportType` OFF |
| `*.config.{ts,js,mjs,cjs}` | `noConsole` OFF |

### Excludes globales

`node_modules`, `dist`, `.astro`, `coverage`, `.pnpm-store`, `public` (assets binarios).

### Formatter

- `indentStyle: space`, `indentWidth: 2`, `lineWidth: 80`
- JS/TS: `quoteStyle: single`, `semicolons: asNeeded`, `trailingCommas: all`, `arrowParentheses: always`, `bracketSpacing: true`
- JSON: `trailingCommas: none`

## TypeScript

- **TypeScript-only** — todo codigo de aplicacion en `.ts`, `.tsx` o
  bloques `<script lang="ts">` / frontmatter TS dentro de `.astro`.
  **JavaScript nativo PROHIBIDO** (`.js`, `.jsx`, `.mjs`, `.cjs`) en
  `src/` y `tests/`. La unica excepcion son configs de root que el
  toolchain exige como `.mjs` (caso a caso, documentado).
- `strict: true` obligatorio
- `noImplicitAny`, `strictNullChecks`, `strictPropertyInitialization`,
  `noUnusedLocals`, `noUnusedParameters`, `noUncheckedIndexedAccess`,
  `verbatimModuleSyntax`
- Type-only imports/exports: `import type { Foo } from './bar'`
- **`any` PROHIBIDO** — sin excepciones, ni en tests ni en mocks. Usar
  `unknown` con narrow (type guard, `typeof`, `instanceof`), `satisfies`
  para preservar literal inference, o Zod `z.infer` cuando hay validacion
  runtime.
- `tsconfig.json` extiende de `astro/tsconfigs/strict` + base custom del
  monorepo (que agrega `noUncheckedIndexedAccess` + `verbatimModuleSyntax`)
- Detalle TS 6: `.claude/rules/typescript.md` + skill `typescript-6`

## Astro-specific gotchas

- `import.meta.env.PUBLIC_*`: variables expuestas al cliente (visibles en bundle)
- `import.meta.env.<otra>`: variables solo build-time (NO exponer secretos via PUBLIC_)
- Astro Islands: `client:load`, `client:idle`, `client:visible` controlan hidratacion — preferir `client:visible` o `client:idle` para reducir JS inicial
- `set:html` solo con contenido sanitizado (XSS risk — `noDangerouslySetInnerHtml` activo en Biome)
- Imagenes: usar `<Image>` o `<Picture>` de `astro:assets` para optimizacion automatica

## Testing

- Framework: Vitest + happy-dom para unit tests
- Path mirroring: `src/X/Y.ts` -> `tests/unit/X/Y.test.ts`
- Componentes `.astro`: testear como string parseado (no se renderizan en JSDOM)
- Coverage v8 >= 80% (statements, branches, functions, lines) en archivos modificados
- Patron AAA en el cuerpo + **BDD-style en `it()`** (Given/When/Then)

```typescript
import { describe, expect, it } from 'vitest'
import { formatDate } from '@/lib/format-date'

describe('formatDate', () => {
  it('Given YYYY-MM and locale "es" When format Then returns Spanish month + year', () => {
    // Arrange
    const input = '2024-01'

    // Act
    const result = formatDate(input, 'es')

    // Assert
    expect(result).toBe('enero 2024')
  })
})
```

Reglas:

- `it()` empieza con `Given ... When ... Then ...`
- Asserts EXACTOS: `expect(result).toBe('enero 2024')`, NUNCA `expect(result.length).toBeGreaterThan(0)`

### Feature tests / E2E (Playwright, opcional)

Solo para flujos completos del usuario que no se puedan testear unit:

- Suite en `tests/e2e/` con baseURL `http://localhost:4321` (default Astro dev)
- Ejecutar: `pnpm exec playwright test`
- NO se ejecutan en CI por costo si son pesados; on-demand antes de merge

## Verificacion

```bash
pnpm exec biome check .                # lint + format
pnpm exec tsc --noEmit                 # typecheck TS
pnpm exec astro check                  # typecheck Astro
pnpm exec vitest run                   # unit tests
pnpm exec vitest run --coverage        # con coverage
pnpm run build                         # build estatico a dist/
pnpm run preview                       # preview del build
```

## Anti-patterns prohibidos

- ❌ Fonts desde Google Fonts CDN (usar `@fontsource/*` self-hosted)
- ❌ `any` en TypeScript (usar `unknown` con narrow)
- ❌ Hex colors inline (usar tokens del DS via CSS vars)
- ❌ `set:html` con contenido no sanitizado
- ❌ `import.meta.env.SECRET_KEY` referenciado en codigo del cliente
- ❌ Mezclar npm/yarn con pnpm
- ❌ Hidratacion innecesaria (`client:load` cuando `client:visible` o `client:idle` funcionan)
- ❌ Olvidar test mirror al crear archivo en `src/lib/`
