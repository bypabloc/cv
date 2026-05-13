#!/bin/bash
# SessionStart hook (matcher: startup).
# Verifica health basico al inicio de cada sesion nueva (no en compactacion).
# - pnpm disponible?
# - node_modules instalado?
# - Branch actual + estado git?
#
# Si algo critico falla, emite warning visible al stderr pero NO bloquea
# (sigue siendo SessionStart, no debe abortar la sesion).

set -u

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$HOOK_DIR/_lib.sh"

cd "$CLAUDE_PROJECT_DIR" || exit 0

WARNINGS=0

echo "[session-start-check] Verificando estado del proyecto..." >&2

# 1. pnpm disponible?
if ! have_pnpm; then
  echo "[session-start-check] WARNING: pnpm no esta en PATH." >&2
  echo "  Instalar pnpm via corepack: corepack enable && corepack prepare pnpm@latest --activate" >&2
  WARNINGS=$((WARNINGS + 1))
else
  echo "[session-start-check] pnpm OK ($(pnpm --version 2>/dev/null))." >&2
fi

# 2. node_modules instalado?
if [ -f "package.json" ] && [ ! -d "node_modules" ]; then
  echo "[session-start-check] WARNING: package.json existe pero falta node_modules." >&2
  echo "  Ejecuta: pnpm install" >&2
  WARNINGS=$((WARNINGS + 1))
fi

# 3. Branch actual + cambios pendientes.
BRANCH="$(current_branch)"
if [ -n "$BRANCH" ]; then
  STATUS_COUNT="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  echo "[session-start-check] Rama: $BRANCH | Cambios pendientes: $STATUS_COUNT" >&2

  if on_protected_branch; then
    echo "[session-start-check] WARNING: estas en rama protegida ($BRANCH)." >&2
    echo "  Para implementar features: git checkout -b feature/<nombre>" >&2
    WARNINGS=$((WARNINGS + 1))
  fi
fi

# 4. Resumen final.
if [ "$WARNINGS" -gt 0 ]; then
  echo "[session-start-check] $WARNINGS warning(s). Resuelve antes de empezar trabajo serio." >&2
else
  echo "[session-start-check] Todo OK. Listo para trabajar." >&2
fi

exit 0
