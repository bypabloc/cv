---
description: "Reglas transversales para el proyecto portfolio: stack Astro 6 + TypeScript + Biome + Vitest + Playwright, ejecucion local con pnpm, estructura del repo."
---

# Reglas Generales - Portfolio

> Indice de reglas transversales. Detalles tecnicos en archivos especificos.

## Proyecto

- Portfolio / CV personal de Pablo Contreras
- Output: site estatico desplegable en cualquier hosting CDN (Vercel, Netlify, Cloudflare Pages, GitHub Pages)
- Sin backend, sin DB, sin auth
- Stack: Astro 6 + TypeScript 6 + Biome v2 + Vitest + Playwright
- Package manager: pnpm

## Ejecucion (CRITICO)

- Ejecucion local directa con pnpm (no Docker)
- NUNCA mezclar npm/yarn — solo pnpm
- Node version: la declarada en `package.json` `engines` o `.nvmrc` (default 22+)
- Comandos base:

```bash
pnpm install               # instalar deps
pnpm run dev               # dev server con HMR
pnpm run build             # build estatico a dist/
pnpm run preview           # preview del build
pnpm exec biome check .    # lint + format check
pnpm exec biome check --write .   # lint + format autofix
pnpm exec tsc --noEmit     # typecheck TypeScript
pnpm exec astro check      # typecheck Astro (.astro files)
pnpm exec vitest run       # unit tests
pnpm exec playwright test  # E2E tests (si aplica)
```

## Codigo (resumen — ver rules especificas)

- **Lenguaje obligatorio**: TypeScript en todo codigo de aplicacion (`.ts`,
  `.tsx`, `<script lang="ts">` en `.astro`). JavaScript nativo (`.js`,
  `.jsx`, `.mjs`, `.cjs`) PROHIBIDO salvo configs de root que el toolchain
  exija como `.mjs` (excepcion acotada). Detalle: `.claude/rules/typescript.md`.
- **Type safety**: TS 6 strict + `noUncheckedIndexedAccess` +
  `verbatimModuleSyntax`. `any` PROHIBIDO sin excepciones — usar `unknown`
  con narrow, `satisfies` para preservar inference, o Zod schema con
  `z.infer`. Tests/mocks tampoco pueden usar `any`.
- **Estructura**: convenciones en `.claude/rules/astro-landing.md`
- **Design system**: tokens, fonts, theme dark/light en `.claude/rules/design-system.md`
- **Docstrings**: estandar agnostico de lenguaje en `.claude/rules/docstring-standard.md`
- **Naming**: componentes Astro PascalCase, utilities kebab-case, branches feature/fix con `/`
- **Tokens del DS**: nunca hex inline en componentes, usar CSS vars
- **Fonts**: self-hosted via `@fontsource/*`, nunca Google Fonts CDN
- **Archivos temporales**: en `./tmp/` del proyecto, NUNCA `/tmp/` del sistema
- **Sin credenciales en codigo**: usar `.env` (no committeado) o variables de entorno del hosting

## Estructura tipica del repo

```text
.
├── src/
│   ├── pages/           # Rutas Astro (.astro)
│   ├── layouts/         # Layouts compartidos
│   ├── components/      # Componentes reutilizables
│   ├── content/         # Content collections (opcional)
│   ├── lib/             # Utilities, formatters, validators
│   ├── styles/          # CSS globales, tokens, typography
│   └── env.d.ts
├── public/              # Assets estaticos (favicon, og-image, etc.)
├── tests/
│   ├── unit/            # Vitest, mirror de src/
│   └── e2e/             # Playwright (opcional)
├── docs/                # Documentacion del proyecto (CV, knowledge tree)
├── .claude/             # Configuracion del harness
├── astro.config.ts
├── biome.json
├── tsconfig.json
├── vitest.config.ts
├── package.json
└── pnpm-lock.yaml
```

## Git

- Conventional Commits obligatorio (ver `git-workflow.md`)
- Branches: `feature/`, `fix/`, `chore/`, `docs/` con separador `/`
- Quality gates: ver `git-hooks.md`
- NUNCA atribucion de IA en commits/PRs

## Testing (resumen — ver rules especificas)

- **Unit**: Vitest + happy-dom, path mirroring de `src/` a `tests/unit/`
- **E2E**: Playwright (opcional, solo flujos completos)
- Coverage minimo 80% per-file en archivos modificados
- Patron AAA + BDD-style (`Given/When/Then`) en `it()`
- Asserts EXACTOS (`toBe(42)`, no `toBeGreaterThan(0)`)
- Detalles: `astro-landing.md`
