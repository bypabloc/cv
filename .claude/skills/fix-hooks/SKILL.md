---
name: fix-hooks
description: >
  Runs git hooks (pre-commit/pre-push) and iteratively repairs ALL detected
  errors. ALWAYS invoke for git hook repair or quality gate fix. Triggers:
  "fix commit", "fix push", "fix hook", "reparar hook", "arreglar hook",
  "pre-commit", "pre-push", "quality gates", "fix lint", "fix conformance",
  "fix coverage", "fix typecheck".
user-invocable: true
allowed-tools: Bash(*), Read, Edit, Write, Grep, Glob
argument-hint: "commit | push"
metadata:
  version: "2.1"
---

# Reparador de Errores de Git Hooks

Ejecutar el hook indicado en bucle, reparando todos los errores hasta exit code 0.

## Argumento

- `commit` (default) — ejecuta `.git-hooks/pre-commit`
- `push` — ejecuta `.git-hooks/pre-push`

## Proceso

1. Ejecutar el hook directamente (tienen shebang, NO usar python):

**Pre-commit:**

```bash
./.git-hooks/pre-commit
```

**Pre-push** (output puede ser largo):

```bash
mkdir -p ./tmp
./.git-hooks/pre-push 2>&1 | tee ./tmp/pre-push-output.log; echo "EXIT_CODE: ${PIPESTATUS[0]}"
```

Si los hooks no existen en `.git-hooks/`, el proyecto todavia no tiene
quality gates configurados — sugerir crearlos o correr las herramientas
directamente (`pnpm exec biome check`, `pnpm exec vitest run`,
`pnpm exec astro check`).

2. Si exit code != 0, analizar errores del output:
   - Identificar archivos y tipos de error (Biome, Vitest, astro-check, tsc)
   - Priorizar: conformance (Biome) > typecheck (tsc/astro check) > tests (Vitest) > coverage

3. Reparar errores:
   - **Biome**: ejecutar `pnpm exec biome check --write .` para auto-fix; ediciones puntuales con Edit cuando un fix no es seguro
   - **TypeScript**: corregir tipos con Edit (output de `tsc --noEmit` muestra archivo:linea)
   - **Astro check**: corregir errores reportados (frontmatter, props, JSX en `.astro`)
   - **Tests Vitest**: leer test y source, corregir logica
   - **Coverage < 80%**: agregar tests para archivos descubiertos

4. Re-ejecutar el hook. Repetir hasta exit code 0.

## Reglas

- NO usar `--no-verify` ni `biome-ignore` para saltarse errores
- NO declarar exito hasta exit code 0
- Mostrar progreso: "Iteracion N: X errores"
- Si un error requiere intervencion manual (decision de diseno), documentarlo y preguntar al usuario
- Auto-fix de Biome con `--write` es seguro; revisar el diff antes de commit

## Contexto del proyecto

- Stack: Astro 6 + TypeScript 6 + Biome v2 + Vitest + pnpm
- Biome config: `biome.json` en raiz
- Vitest config: `vitest.config.ts`
- TypeScript config: `tsconfig.json`
- Hooks: `.git-hooks/pre-commit` y `.git-hooks/pre-push` (si existen)

## Comandos clave

```bash
# Lint / format autofix
pnpm exec biome check --write .

# Typecheck TypeScript
pnpm exec tsc --noEmit

# Typecheck Astro
pnpm exec astro check

# Unit tests
pnpm exec vitest run

# Unit tests con coverage
pnpm exec vitest run --coverage

# Build (verifica que el proyecto compila para produccion)
pnpm run build
```
