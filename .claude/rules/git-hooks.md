---
description: "Git hooks versionados en .git-hooks/ con quality gates: pre-commit (conformance + typecheck) y pre-push (tests + build)."
globs: ".git-hooks/**,**/pre-commit,**/pre-push"
---

# Git Hooks - Quality Gates

> Sistema de hooks versionados en `.git-hooks/` para quality gates automaticos.
> Aplicable cuando el repo tiene git hooks configurados. Si todavia no existen
> los archivos en `.git-hooks/`, esta regla describe el contrato esperado.

## Arquitectura

- Hooks versionados en `.git-hooks/` (NO `.git/hooks/`)
- Activar: `git config core.hooksPath .git-hooks`
- Configuracion de pasos: `.git-hooks/config.json` (enable/disable por paso) — opcional

## Pre-commit (archivos en staging — rapido)

Pasos en orden, solo se ejecutan si hay archivos relevantes:

1. **conformance (biome)** — Biome lint + format check sobre staged
2. **typecheck-ts** — `tsc --noEmit` (TypeScript strict)
3. **typecheck-astro** — `astro check` sobre archivos `.astro` modificados
4. **unit tests** — Vitest sobre tests relacionados con archivos modificados (`vitest run --changed`)

Build y E2E **NO** se ejecutan en pre-commit para mantener el commit liviano.

## Pre-push (verificacion completa)

Mismos pasos que pre-commit MAS:

5. **coverage** — Vitest con `--coverage`, threshold per-file >= 80% en archivos modificados
6. **build** — `pnpm run build` debe completar sin errores

E2E (Playwright) sigue siendo opt-in via env var (corre lento, decide el dev).

## Mirror y per-file coverage

| Source root | Test mirror root | Coverage threshold |
|-------------|------------------|--------------------|
| `src/lib/<X>.ts` | `tests/unit/lib/<X>.test.ts` | >= 80% per-file |
| `src/components/<X>.astro` | `tests/unit/components/<X>.test.ts` | >= 80% per-file |
| `src/pages/<X>.astro` | E2E coverage (Playwright) | n/a |

Reglas:

- `.astro` source mapea a `.test.ts` (mismo nombre, distinta extension)
- Source modificado **sin mirror** en `tests/unit/` puede fallar el gate (TDD enforcement)
- Coverage < 80% en cualquier source modificado = hook falla
- Vitest usa `--coverage.include=<source>` para evitar contar archivos no relevantes

## Skip steps

- Saltar pasos especificos (no recomendado): `SKIP_STEPS="coverage,build" git commit -m "msg"`
- Saltar todo (emergencias): `git commit --no-verify` — POLITICA: prohibido por hook PreToolUse
- REQUISITO: pnpm + node_modules instalados localmente

## Deteccion de archivos

Los hooks usan `git diff --cached --name-only` (pre-commit) o
`git diff --name-only origin/<base>...HEAD` (pre-push) para detectar
archivos afectados. Solo ejecutan pasos relevantes al tipo de archivo.

## CI

- CI workflow en `.github/workflows/ci.yml` (si existe) reutiliza la misma logica
- Trigger: PRs a `main`/`master`/`dev`
- E2E (Playwright) opt-in via env var en CI tambien
- act (nektos/act) para testing local del workflow CI (`/github-actions` skill)
