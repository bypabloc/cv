#!/usr/bin/env bash
# Comprime un GLB de personaje (salida de build-character.py) para produccion:
# resize de texturas a 512 + WebP (decode nativo del browser, sin transcoder)
# + Draco (geometria). Sin `simplify` (dañaria los skin weights del rig).
# Resultado tipico: ~60 MB -> ~0.5 MB, con la cara pintada intacta.
#
# Uso: compress-glb.sh <entrada.glb> <salida.glb> [tamano_textura]
set -euo pipefail

IN="${1:?falta <entrada.glb>}"
OUT="${2:?falta <salida.glb>}"
SIZE="${3:-512}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

GT="pnpm dlx @gltf-transform/cli"
# el journey usa MeshToonMaterial (solo baseColorTexture). build-character.py
# ya deja SOLO el baseColor en cada material (borra normal/specular/rough en
# Blender). Aca: resize a 512 + webp del baseColor + draco.
$GT resize "$IN" "$TMP/r.glb" --width "$SIZE" --height "$SIZE" >/dev/null
# resample: quita keyframes redundantes de las animaciones (Mixamo baja de
# 60fps a los keyframes necesarios) — el mayor peso del GLB son las anims.
$GT resample "$TMP/r.glb" "$TMP/rs.glb" >/dev/null 2>&1 || cp "$TMP/r.glb" "$TMP/rs.glb"
$GT webp "$TMP/rs.glb" "$TMP/rw.glb" >/dev/null
$GT draco "$TMP/rw.glb" "$OUT" >/dev/null
echo "compressed: $IN -> $OUT ($(stat -c '%s' "$OUT") bytes, tex ${SIZE}px)"
