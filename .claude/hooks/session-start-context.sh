#!/bin/bash
# SessionStart hook (matcher: compact).
# Tras una compactacion de contexto, re-inyecta las reglas criticas del proyecto
# para que Claude no "olvide" stack, TDD, coverage, etc.
#
# Lo que se imprima a stdout se anade al contexto de la sesion.

set -u

cat <<'EOF'
[Reglas criticas re-inyectadas tras compactacion]

Proyecto: portfolio / CV personal en Astro 6 + TypeScript + Biome + Vitest + Playwright.

1. Stack puro frontend: NO hay Django, NO hay Docker, NO hay backend.
2. Package manager: pnpm. NUNCA mezclar con npm/yarn.
3. Credenciales solo via `.env`, nunca hardcoded.
4. Archivos temporales en `./tmp/`, nunca `/tmp/` del sistema.
5. Conventional Commits en espanol: `feat(scope): descripcion`.
6. TDD obligatorio: source modificado SIN test mirror en tests/unit/ puede fallar verify.
7. Coverage minimo 80% per-file en archivos modificados (excluir configs y fixtures).
8. NUNCA force push en master, main, dev, release.
9. NUNCA atribucion de IA en commits/PRs (politica de empresa).

Comandos clave:
  pnpm install                 # instalar deps
  pnpm run dev                 # dev server Astro
  pnpm run build               # build estatico
  pnpm exec biome check .      # lint
  pnpm exec biome check --write . # lint + format autofix
  pnpm exec astro check        # typecheck Astro
  pnpm exec tsc --noEmit       # typecheck TS
  pnpm exec vitest run         # unit tests
  pnpm exec playwright test    # E2E tests (si aplica)

Reglas detalladas: .claude/rules/
EOF

exit 0
