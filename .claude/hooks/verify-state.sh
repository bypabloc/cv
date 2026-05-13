#!/bin/bash
# Stop hook.
# Al final de cada turno de Claude:
# 1. Lista archivos modificados (incluye untracked) en el repo.
# 2. Detecta source files SIN test mirror (TDD enforcement, src/ -> tests/unit/).
# 3. Sugiere comandos de verificacion accionables al stderr.
#
# El output va al stderr para que Claude lo vea como feedback automatico
# y pueda actuar en el siguiente turno sin que el usuario lo pida.
#
# NO bloquea (exit 0 siempre).

set -u

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$HOOK_DIR/_lib.sh"

cd "$CLAUDE_PROJECT_DIR" || exit 0

# Archivos modificados (tracked) + nuevos (untracked, no ignorados).
MODIFIED="$(git diff --name-only HEAD 2>/dev/null)"
UNTRACKED="$(git ls-files --others --exclude-standard 2>/dev/null)"
STAGED="$(git diff --cached --name-only 2>/dev/null)"

ALL_FILES="$(printf '%s\n%s\n%s\n' "$MODIFIED" "$UNTRACKED" "$STAGED" | sort -u | grep -v '^$')"

# Si no hay cambios, salir silenciosamente.
[ -z "$ALL_FILES" ] && exit 0

CHANGED_COUNT="$(echo "$ALL_FILES" | wc -l | tr -d ' ')"
STAGED_COUNT="$(echo "$STAGED" | grep -v '^$' | wc -l | tr -d ' ')"

# Clasifica por carpeta.
SRC_FILES=""
CLAUDE_FILES=""
DOCS_FILES=""
CONFIG_FILES=""

while IFS= read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    src/*) SRC_FILES="${SRC_FILES}${f}"$'\n' ;;
    .claude/*) CLAUDE_FILES="${CLAUDE_FILES}${f}"$'\n' ;;
    docs/*) DOCS_FILES="${DOCS_FILES}${f}"$'\n' ;;
    *.config.*|*.json|*.yml|*.yaml|biome.json|astro.config.*|tsconfig.json|vitest.config.*|playwright.config.*) CONFIG_FILES="${CONFIG_FILES}${f}"$'\n' ;;
  esac
done <<< "$ALL_FILES"

# Funcion: dado un source file en src/, calcula su mirror de test esperado en tests/unit/.
mirror_for() {
  local src="$1"
  local base
  case "$src" in
    src/*)
      base="${src#src/}"
      case "$base" in
        *.astro) base="${base%.astro}.test.ts" ;;
        *.tsx) base="${base%.tsx}.test.tsx" ;;
        *.ts) base="${base%.ts}.test.ts" ;;
        *) echo ""; return ;;
      esac
      echo "tests/unit/$base"
      ;;
    *) echo "" ;;
  esac
}

# Detecta source files sin mirror (skip si ya es test).
MISSING_MIRRORS=""

while IFS= read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    */tests/*|*/__tests__/*) continue ;;
  esac
  mirror="$(mirror_for "$f")"
  [ -z "$mirror" ] && continue
  if [ ! -f "$CLAUDE_PROJECT_DIR/$mirror" ]; then
    MISSING_MIRRORS="${MISSING_MIRRORS}  - SOURCE: $f"$'\n'"    MIRROR: $mirror"$'\n'
  fi
done <<< "$SRC_FILES"

# Output al stderr.
echo "[verify-state] $CHANGED_COUNT archivo(s) cambiado(s), $STAGED_COUNT staged." >&2

if [ -n "$SRC_FILES" ]; then
  echo "[verify-state] src/ afectado. Verificacion sugerida:" >&2
  echo "  pnpm exec biome check ." >&2
  echo "  pnpm exec tsc --noEmit" >&2
  echo "  pnpm exec astro check" >&2
  echo "  pnpm exec vitest run --changed" >&2
fi

if [ -n "$CONFIG_FILES" ]; then
  echo "[verify-state] configs afectados. Verificacion sugerida:" >&2
  echo "  pnpm run build         # build estatico Astro" >&2
fi

if [ -n "$CLAUDE_FILES" ]; then
  echo "[verify-state] .claude/ afectado. Verificar:" >&2
  echo "  python3 -m json.tool .claude/settings.json > /dev/null  # JSON valido" >&2
  echo "  bash -n .claude/hooks/<modificado>.sh                   # syntax shell ok" >&2
fi

if [ -n "$MISSING_MIRRORS" ]; then
  echo "" >&2
  echo "[verify-state] FALTAN test mirrors (TDD enforcement):" >&2
  printf '%s' "$MISSING_MIRRORS" >&2
  echo "" >&2
  echo "  Crea cada mirror con tests reales (no placeholders) antes del push." >&2
fi

exit 0
