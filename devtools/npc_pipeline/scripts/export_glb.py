"""Blender headless: export a rigged .blend to a raw (uncompressed) .glb.

Run via devtools (encadena automaticamente la compresion glTF-Transform
Meshopt tras este paso — ver npc_pipeline/main.py):
  python devtools/run.py npc_pipeline export \
    --input=<npc-rigged.blend> --output=<npc-base.glb>

Direct invocation (solo el export nativo, sin comprimir):
  blender --background --python export_glb.py -- \
    --input=<X> --output=<raw.glb>

Usa el exportador glTF2 NATIVO de Blender (incluido, sin addon extra),
con ``export_animation_mode='ACTIONS'`` para exportar TODAS las
acciones del armature (idle + walk, ver animate.py) como clips glTF
separados — el default de Blender solo exporta la accion activa. La
compresion Meshopt (necesaria por los clips de animacion embebidos) la
aplica glTF-Transform CLI como segundo paso, fuera de Blender — ver
.claude/docs/journey-npc-realism/02-export-y-threejs-integracion.md.
"""

from pathlib import Path
import sys

import bpy


sys.path.insert(0, str(Path(__file__).resolve().parent))
from _argv import parse_args


def main() -> None:
    args = parse_args()
    input_path = args['input']
    output_path = args['output']

    bpy.ops.wm.open_mainfile(filepath=input_path)

    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        export_animations=True,
        export_animation_mode='ACTIONS',
        export_skins=True,
        export_apply=True,
    )
    print(f'Export nativo (sin comprimir) en {output_path}')


if __name__ == '__main__':
    main()
