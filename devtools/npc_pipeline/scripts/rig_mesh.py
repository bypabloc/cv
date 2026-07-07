"""Blender headless: rig the MPFB2 human with its built-in Rigify flow.

Run via devtools:
  python devtools/run.py npc_pipeline rig \
    --input=<npc-base.blend> --output=<npc-rigged.blend>

Direct invocation:
  blender --background --python rig_mesh.py -- \
    --input=<X> --output=<Y>

Spike T4 (ver docs/specs/journey-npc-realism/mpfb2-api-discovery.md)
descubrio que MPFB2 expone ``bpy.ops.mpfb.add_rigify_rig()``: un solo
operator que (1) agrega un metarig de Rigify YA AJUSTADO a las
proporciones reales del humano activo, (2) lo genera (equivalente a
``bpy.ops.pose.rigify_generate()``), y (3) parentea + skinnea la malla
al rig resultante con pesos reales (333 vertex groups, Armature
modifier) — todo en un paso, sin necesitar el metarig generico +
snap manual de huesos que se planeaba antes del spike.
"""

from pathlib import Path
import sys

import bpy


sys.path.insert(0, str(Path(__file__).resolve().parent))
from _argv import parse_args


def _find_human_object() -> bpy.types.Object:
    human = bpy.data.objects.get('Human')
    if human is None or human.type != 'MESH':
        msg = "No se encontro el objeto MESH 'Human' en el .blend de entrada"
        raise RuntimeError(msg)
    return human


def main() -> None:
    args = parse_args()
    input_path = args['input']
    output_path = args['output']

    bpy.ops.wm.open_mainfile(filepath=input_path)

    human = _find_human_object()
    bpy.context.view_layer.objects.active = human
    bpy.ops.object.select_all(action='DESELECT')
    human.select_set(True)

    result = bpy.ops.mpfb.add_rigify_rig()
    if result != {'FINISHED'}:
        msg = f'mpfb.add_rigify_rig fallo: {result}'
        raise RuntimeError(msg)

    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f'Rig guardado en {output_path}')


if __name__ == '__main__':
    main()
