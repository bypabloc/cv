#!/bin/bash
# PostToolBatch hook.
# Tras un lote de tools (multiples Edit/Write seguidos), corre lint check
# rapido sobre los archivos modificados en git para dar feedback al modelo.
#
# NO bloquea: solo loguea al stderr para que Claude lo vea como feedback informativo.

set -u

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$HOOK_DIR/_lib.sh"

have_pnpm || exit 0

# Lista archivos modificados (staged + unstaged + untracked no ignorados).
CHANGED="$(cd "$CLAUDE_PROJECT_DIR" && {
  git diff --name-only HEAD 2>/dev/null
  git ls-files --others --exclude-standard 2>/dev/null
} | sort -u | grep -v '^$' | head -30)"
[ -z "$CHANGED" ] && exit 0

# Filtra solo archivos que Biome puede chequear (TS/Astro/JS/CSS/JSON)
RELEVANT="$(echo "$CHANGED" | grep -E '\.(ts|tsx|astro|js|jsx|mjs|cjs|json|jsonc|css)$' || true)"
[ -z "$RELEVANT" ] && exit 0

cd "$CLAUDE_PROJECT_DIR" || exit 0

# Biome sobre archivos modificados, head limitada para no inundar stderr.
RESULT="$(echo "$RELEVANT" | xargs -r pnpm exec biome check --no-errors-on-unmatched 2>&1 | head -40 || true)"
if echo "$RESULT" | grep -qE "^[[:space:]]*(error|warning)[[:space:]:]"; then
  echo "[lint-check biome]" >&2
  echo "$RESULT" >&2
fi

exit 0
