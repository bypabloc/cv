#!/usr/bin/env bash
# progress-cleanup.sh — Stop hook complementario.
#
# Al cerrar sesion:
#   1. Si current.md tiene contenido sustantivo, recordar al usuario mover
#      a history.md
#   2. Listar archivos temporales en docs/progress/ (explore_*, impl_*, review_*)
#      como recordatorio - NO los borra automatico (el usuario decide)
#   3. Limpia snapshots viejos (>7 dias) de pre-compact
#
# NO bloquea (exit 0 siempre). Output a stderr para que Claude lo vea.

set -u

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$HOOK_DIR/_lib.sh"

cd "$CLAUDE_PROJECT_DIR" 2>/dev/null || exit 0

# 1. current.md con contenido sustantivo?
if [ -f docs/progress/current.md ]; then
  # Cuenta lineas no vacias y no template (excluye headers, ">", "_..._")
  CONTENT_LINES="$(grep -vE '^\s*$|^#|^>|^_|^- \*\*|^\| ' docs/progress/current.md 2>/dev/null | grep -v '^- \.\.\.$' | wc -l | tr -d ' ')"
  if [ "$CONTENT_LINES" -gt 3 ]; then
    echo "[progress-cleanup] docs/progress/current.md tiene contenido sustantivo." >&2
    echo "  Considera mover el resumen a docs/progress/history.md y vaciar current.md" >&2
    echo "  antes de cerrar la sesion (ver harness-protocol.md)." >&2
  fi
fi

# 2. Archivos temporales de subagentes
TEMP_FILES="$(find docs/progress -maxdepth 1 -type f \( -name 'explore_*.md' -o -name 'impl_*.md' -o -name 'review_*.md' -o -name 'optim_*.md' -o -name 'refactor_*.md' -o -name 'audit_*.md' -o -name 'debug_*.md' \) 2>/dev/null)"

if [ -n "$TEMP_FILES" ]; then
  TEMP_COUNT="$(echo "$TEMP_FILES" | wc -l | tr -d ' ')"
  echo "[progress-cleanup] $TEMP_COUNT archivo(s) temporal(es) de subagentes en docs/progress/:" >&2
  echo "$TEMP_FILES" | sed 's/^/  - /' >&2
  echo "  Si la sesion se cierra, considera limpiar:" >&2
  echo "  rm -f docs/progress/explore_*.md docs/progress/impl_*.md docs/progress/review_*.md" >&2
fi

# 3. Limpia snapshots de pre-compact viejos (>7 dias)
if command -v find >/dev/null 2>&1; then
  OLD_SNAPSHOTS="$(find docs/progress -maxdepth 1 -name '.snapshot_*.md' -mtime +7 2>/dev/null)"
  if [ -n "$OLD_SNAPSHOTS" ]; then
    OLD_COUNT="$(echo "$OLD_SNAPSHOTS" | wc -l | tr -d ' ')"
    echo "$OLD_SNAPSHOTS" | xargs rm -f 2>/dev/null
    echo "[progress-cleanup] Eliminados $OLD_COUNT snapshot(s) >7 dias." >&2
  fi
fi

exit 0
