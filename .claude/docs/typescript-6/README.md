# TypeScript 6 — Knowledge Tree

> Documentacion consolidada de TypeScript 6.0 (GA marzo 23, 2026) para el
> portfolio. TS 6 es la ultima version JavaScript-based; TS 7.0 (finales
> 2026) sera reescrita en Go con 10x mejor performance. Codigo escrito
> hoy en TS 6 idiomatico = upgrade a TS 7 sin friccion.

## Cuando leer

| Tema | Archivo |
|------|---------|
| Breaking changes 5.x -> 6.0 + codemod ts5to6 | [01-breaking-changes.md](01-breaking-changes.md) |
| Features nuevos (native node .ts, isolatedDeclarations, using/await using, satisfies, project references, module Preserve) | [02-features.md](02-features.md) |
| Strict mode + flags adicionales recomendados | [03-strict-mode.md](03-strict-mode.md) |
| tsconfig canonicos por contexto (Astro / Next / package) | [04-tsconfig.md](04-tsconfig.md) |

## Reglas criticas (enforced en `.claude/rules/typescript.md`)

- **SIEMPRE TypeScript** — el portfolio prohibe JavaScript nativo (`.js`,
  `.jsx`, `.mjs`, `.cjs`) excepto archivos de configuracion del root
  cuando una herramienta lo requiera. Codigo de aplicacion siempre `.ts` /
  `.tsx` / `.astro`.
- **SIEMPRE typing explicito** — `any` esta PROHIBIDO. Usar `unknown` +
  narrow, o tipos especificos.
- **SIEMPRE strict mode** — `"strict": true` en todo tsconfig.json.
- **SIEMPRE** `"noUncheckedIndexedAccess": true` y
  `"verbatimModuleSyntax": true`.
- **SIEMPRE** `"module": "ESNext"` + `"moduleResolution": "bundler"` para
  apps Astro y dashboard Next.js.
- **SIEMPRE** listar `@types/*` en `"types": [...]` (TS 6 sin auto-discovery).
- **NUNCA** `any` en codigo de aplicacion. Test/mocks tampoco — usar tipos
  reales del modulo bajo test.
- **NUNCA** `baseUrl` (REMOVIDO en TS 6).
- **NUNCA** `"target": "ES5"` (deprecated).
- **NUNCA** `module Foo { }` syntax (error en TS 6).

## Resumen de versiones

| Hito | Fecha |
|------|-------|
| TS 5.9 (ultima v5) | enero 2026 |
| TS 6.0 beta | 11 febrero 2026 |
| TS 6.0 RC | 24 febrero 2026 |
| **TS 6.0 GA** | **23 marzo 2026** |
| TS 6.0.x patches | marzo-mayo 2026 |
| TS 7.0 preview (Go port) | finales 2026 (TBD) |

## Performance (TS 5.9 -> 6.0)

| Aspecto | Mejora |
|---------|--------|
| Cold build | -47% |
| Incremental rebuild | -40% a -60% |
| Peak memory | -25% |
| Language service latency | -30% |
| `@types` discovery (con `types` listado) | -90% |

## Ecosystem mayo 2026

| Package | Version TS 6-ready |
|---------|--------------------|
| `@types/node` | 24.x |
| `@types/react` | 19.x |
| `astro` | 6.x |
| `next` | 16.x |
| `zod` | 4.x |
| `vitest` | 3.x |
| `biome` | 2.3+ (Biotype) |

## Referencias externas

- [Microsoft DevBlogs — Announcing TypeScript 6.0](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/)
- [TypeScript Handbook — Modules](https://www.typescriptlang.org/docs/handbook/modules/guides/choosing-compiler-options.html)
- [Total TypeScript — tsconfig Cheat Sheet](https://www.totaltypescript.com/tsconfig-cheat-sheet)
- [LogRocket — TypeScript v6 Migration Guide](https://blog.logrocket.com/typescript-v6-migration-guide/)
- [ts5to6 codemod (Andrew Branch)](https://github.com/andrewbranch/ts5to6)
- Research raw (efimero): `tmp/research/typescript-6.md` (992 lineas)
