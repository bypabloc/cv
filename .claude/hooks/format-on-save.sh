#!/bin/bash
# PostToolUse hook (matcher: Edit|Write|MultiEdit).
# Auto-formatea + auto-fixea con Biome sobre el archivo recien editado.
#
# El hook nunca bloquea: si pnpm/biome no esta disponible o el archivo no es
# relevante, retorna 0 silenciosamente. La red de seguridad final son los
# git hooks.

set -u

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$HOOK_DIR/_lib.sh"

FILE_PATH="$(read_file_path_from_stdin)"
[ -z "$FILE_PATH" ] && exit 0

# Path relativo al project root
case "$FILE_PATH" in
  "$CLAUDE_PROJECT_DIR"/*) REL_PATH="${FILE_PATH#"$CLAUDE_PROJECT_DIR"/}" ;;
  /*) REL_PATH="$FILE_PATH" ;;
  *) REL_PATH="$FILE_PATH" ;;
esac

EXT="${FILE_PATH##*.}"

case "$EXT" in
  ts|tsx|astro|js|jsx|mjs|cjs|json|jsonc|css)
    : # relevante para Biome
    ;;
  *)
    exit 0
    ;;
esac

have_pnpm || {
  hook_log "pnpm no disponible, saltando format de $REL_PATH"
  exit 0
}

cd "$CLAUDE_PROJECT_DIR" || exit 0

# Biome corre rapido y autocontenido. Foreground con timeout corto.
timeout 10 pnpm exec biome format --write "$REL_PATH" >/dev/null 2>&1 || \
  hook_log "biome format fallo o timeout en $REL_PATH (no critico)"

# Lint --fix en background; no es critico que termine antes del proximo turno.
( timeout 15 pnpm exec biome check --write --no-errors-on-unmatched "$REL_PATH" >/dev/null 2>&1 ) &
disown

exit 0
