#!/usr/bin/env bash
# pre-compact-snapshot.sh — Hook PreCompact (auto/manual)
#
# Antes de que el modelo compacte la ventana de contexto:
#   1. Snapshot del estado actual de docs/progress/current.md a docs/progress/
#   2. Aviso al usuario en stderr de que se va a compactar
#
# Util para no perder el "scratchpad" cuando auto-compact dispara al 40%
# (configurado via CLAUDE_AUTOCOMPACT_PCT_OVERRIDE en settings.json).

set -u

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$HOOK_DIR/_lib.sh"

cd "$CLAUDE_PROJECT_DIR" 2>/dev/null || exit 0

# Leer el JSON de stdin (matcher: "auto" o "manual")
INPUT=""
if [ ! -t 0 ]; then
  INPUT="$(cat 2>/dev/null || true)"
fi

# Tipo de compact
TYPE="auto"
if [ -n "$INPUT" ] && command -v jq >/dev/null 2>&1; then
  PARSED="$(echo "$INPUT" | jq -r '.matcher // "auto"' 2>/dev/null || echo auto)"
  if [ -n "$PARSED" ]; then
    TYPE="$PARSED"
  fi
fi

TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

echo "" >&2
echo "[pre-compact] Compactacion ($TYPE) en curso a las $TIMESTAMP" >&2

# Snapshot del current.md a un archivo timestamped
if [ -f docs/progress/current.md ]; then
  SNAPSHOT="docs/progress/.snapshot_${TYPE}_$(date '+%Y%m%d_%H%M%S').md"
  cp docs/progress/current.md "$SNAPSHOT" 2>/dev/null && \
    echo "[pre-compact] Snapshot de docs/progress/current.md guardado en $SNAPSHOT" >&2
fi

# Mensaje informativo al modelo (no bloquea)
cat <<JSON
{
  "systemMessage": "Compactando contexto ($TYPE). Snapshot de docs/progress/current.md guardado. Tras compactar, lee docs/progress/current.md para recuperar contexto reciente."
}
JSON

exit 0
