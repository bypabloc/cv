#!/bin/bash
# PreToolUse hook (matcher: Edit|Write|MultiEdit).
# Bloquea ediciones de archivos sensibles (env, secrets, keys).
#
# Si detecta un path protegido: exit 2 + mensaje al stderr -> el harness
# rechaza la operacion y muestra el motivo.

set -u

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
source "$HOOK_DIR/_lib.sh"

FILE_PATH="$(read_file_path_from_stdin)"
[ -z "$FILE_PATH" ] && exit 0

BASENAME="$(basename "$FILE_PATH")"

# Patrones bloqueados (comparacion sobre basename Y path completo)
PROTECTED_BASENAMES=(".env" "credentials.json" "secrets.json" "service-account.json")
PROTECTED_PREFIXES=(".env.")
PROTECTED_PATH_FRAGMENTS=("/.aws/" "/.ssh/" "/.git-hooks/" "/.git/config" "/.git/hooks/")

for p in "${PROTECTED_BASENAMES[@]}"; do
  if [ "$BASENAME" = "$p" ]; then
    echo "Bloqueado: $FILE_PATH es un archivo sensible (.env/secrets/credentials). Editar manualmente." >&2
    exit 2
  fi
done

for p in "${PROTECTED_PREFIXES[@]}"; do
  case "$BASENAME" in
    "$p"*)
      echo "Bloqueado: $FILE_PATH coincide con patron sensible '${p}*'. Editar manualmente." >&2
      exit 2
      ;;
  esac
done

for p in "${PROTECTED_PATH_FRAGMENTS[@]}"; do
  case "$FILE_PATH" in
    *"$p"*)
      echo "Bloqueado: $FILE_PATH esta en directorio sensible ($p). Editar manualmente." >&2
      exit 2
      ;;
  esac
done

# Extensiones de claves criptograficas
case "$BASENAME" in
  *.pem|*.key|*.p12|*.pfx|id_rsa|id_ed25519|id_ecdsa)
    echo "Bloqueado: $FILE_PATH parece una clave criptografica. Editar manualmente." >&2
    exit 2
    ;;
esac

exit 0
