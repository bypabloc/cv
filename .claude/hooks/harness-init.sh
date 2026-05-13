#!/usr/bin/env bash
# harness-init.sh — Gate de inicio de sesion (Harness Engineering)
#
# Inspirado en el patron de BettaTech adaptado al stack Astro 6 + pnpm.
# Diferencia con session-start-check.sh (soft warning):
#   - session-start-check.sh: WARNING, no bloquea
#   - harness-init.sh: BLOQUEA si el proyecto no esta listo
#
# Uso manual:    ./.claude/hooks/harness-init.sh
#
# Verifica:
#   1. Archivos base del arnes existen (docs/progress/, CLAUDE.md opcional)
#   2. Cualquier docs/<modulo>/feature_list.json existente es JSON valido
#   3. pnpm disponible + node_modules presente
#   4. Branch actual NO es protegida (master/main/dev/release)
#   5. docs/progress/ sin temporales viejos
#
# Variables de entorno:
#   HARNESS_INIT_QUIET=1   Suprime [OK], solo muestra [WARN] y [FAIL]
#
# Exit code 0 si todo OK; 1 si hay errores criticos.

set -u

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$HOOK_DIR/_lib.sh"

cd "$CLAUDE_PROJECT_DIR" || {
  echo "[harness-init] FAIL: no se pudo cd a CLAUDE_PROJECT_DIR" >&2
  exit 1
}

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

QUIET="${HARNESS_INIT_QUIET:-0}"

ok()    { [ "$QUIET" = "1" ] && return 0; printf "${GREEN}[OK]${NC}    %s\n" "$1" >&2; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$1" >&2; }
fail()  { printf "${RED}[FAIL]${NC}  %s\n" "$1" >&2; }

EXIT_CODE=0

echo "" >&2
echo "── Harness Init: gate de inicio de sesion ──────────────" >&2
echo "" >&2

# 1. Archivos base del arnes (opcionales — solo warn si faltan)
echo "── 1. Archivos base ────────────────────────────────────" >&2
for f in .claude/settings.json; do
  if [ ! -f "$f" ]; then
    fail "Falta archivo critico: $f"
    EXIT_CODE=1
  else
    ok "Existe $f"
  fi
done
for f in CLAUDE.md docs/progress/current.md docs/progress/history.md; do
  if [ ! -f "$f" ]; then
    warn "Falta archivo recomendado: $f (puedes crearlo si trabajas con harness completo)"
  else
    ok "Existe $f"
  fi
done

# 2. feature_list.json por modulo (validacion de los que existan)
echo "" >&2
echo "── 2. feature_list.json por modulo ─────────────────────" >&2
if command -v python3 >/dev/null 2>&1; then
  if python3 - <<'PY' 2>&1 | sed 's/^/  /' >&2
import json, os, sys, glob
quiet = os.environ.get("HARNESS_INIT_QUIET", "0") == "1"
found = sorted(glob.glob("docs/*/feature_list.json"))
if not found:
    if not quiet:
        print("OK    No hay docs/<modulo>/feature_list.json (proyecto simple sin harness queue)")
    sys.exit(0)
errors = []
total_features = 0
total_in_progress = 0
for path in found:
    try:
        data = json.load(open(path))
    except Exception as e:
        errors.append(f"{path}: JSON invalido ({e})")
        continue
    module = data.get("module", "unknown")
    valid = set(data.get("rules", {}).get("valid_status", ["pending", "in_progress", "done", "blocked"]))
    features = data.get("features", [])
    in_progress = [f for f in features if f.get("status") == "in_progress"]
    if data.get("rules", {}).get("one_feature_at_a_time", False) and len(in_progress) > 1:
        errors.append(f"{path}: {len(in_progress)} features in_progress en modulo '{module}' (max 1)")
        continue
    for f in features:
        if f.get("status") not in valid:
            errors.append(f"{path}: feature {f.get('id')} con estado invalido '{f.get('status')}'")
    total_features += len(features)
    total_in_progress += len(in_progress)
    if not quiet:
        print(f"OK    {path}: modulo='{module}' {len(features)} features ({len(in_progress)} in_progress)")
if errors:
    for e in errors:
        print(f"FAIL  {e}")
    sys.exit(1)
if not quiet:
    print(f"OK    Total: {len(found)} modulos, {total_features} features, {total_in_progress} in_progress")
PY
  then :; else EXIT_CODE=1; fi
else
  warn "python3 no disponible, skipping validacion JSON"
fi

# 3. pnpm + node_modules
echo "" >&2
echo "── 3. Toolchain (pnpm + node_modules) ──────────────────" >&2
if ! have_pnpm; then
  fail "pnpm no esta en PATH"
  warn "Instala via corepack: corepack enable && corepack prepare pnpm@latest --activate"
  EXIT_CODE=1
else
  ok "pnpm $(pnpm --version 2>/dev/null)"
  if [ -f package.json ] && [ ! -d node_modules ]; then
    warn "Falta node_modules. Ejecuta: pnpm install"
  elif [ -f package.json ]; then
    ok "node_modules presente"
  fi
fi

# 4. Branch
echo "" >&2
echo "── 4. Git ────────────────────────────────────────────────" >&2
BRANCH="$(current_branch 2>/dev/null || true)"
if [ -n "$BRANCH" ]; then
  ok "Branch: $BRANCH"
  if on_protected_branch; then
    warn "Estas en rama protegida ($BRANCH)"
    warn "Para implementar features: git checkout -b feature/<nombre>"
  fi
  STATUS_COUNT="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  ok "Cambios pendientes: $STATUS_COUNT"
else
  warn "No estas en un repo git"
fi

# 5. Archivos temporales en docs/progress/
echo "" >&2
echo "── 5. docs/progress/ ────────────────────────────────────" >&2
if [ -d docs/progress ]; then
  TEMP_FILES_COUNT="$(find docs/progress -maxdepth 1 -type f \( -name 'explore_*.md' -o -name 'impl_*.md' -o -name 'review_*.md' \) 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$TEMP_FILES_COUNT" -gt 0 ]; then
    warn "Hay $TEMP_FILES_COUNT archivos temporales de subagentes en docs/progress/"
    warn "Si no hay sesion activa, considera limpiar con: rm -f docs/progress/explore_*.md docs/progress/impl_*.md docs/progress/review_*.md"
  else
    ok "docs/progress/ limpio (sin temporales)"
  fi
else
  warn "docs/progress/ no existe (opcional, crea cuando uses harness queue)"
fi

# Resumen
echo "" >&2
echo "── Resumen ──────────────────────────────────────────────" >&2
if [ "$EXIT_CODE" -eq 0 ]; then
  ok "Entorno listo. Puedes empezar a trabajar."
else
  fail "Entorno NO esta listo. Resuelve los errores antes de avanzar."
fi
echo "" >&2

exit "$EXIT_CODE"
