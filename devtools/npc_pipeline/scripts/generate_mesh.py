"""Blender headless: generate the base humanoid mesh (MPFB2) + preview.

Run via devtools:
  python devtools/run.py npc_pipeline generate-mesh \
    --output=<path.blend> [--preview-dir=<dir>]

Direct invocation:
  blender --background --python generate_mesh.py -- \
    --output=<path.blend> --preview-dir=<dir>

Usa ``bpy.ops.mpfb.create_human()`` (spike T4 completado corriendo el
pipeline real — ver
docs/specs/journey-npc-realism/mpfb2-api-discovery.md): sin parametros,
crea un objeto ``Human`` MESH con la topologia MakeHuman real (~19158
vertices, altura ~1.66m, pies en z=0). El objeto ``Cube`` default de la
escena de arranque de Blender se borra (no es parte del humano).
"""

from pathlib import Path
import sys

import bpy


sys.path.insert(0, str(Path(__file__).resolve().parent))
from _argv import parse_args


def _remove_default_cube() -> None:
    cube = bpy.data.objects.get('Cube')
    if cube is not None:
        bpy.data.objects.remove(cube, do_unlink=True)


def _create_base_mesh() -> bpy.types.Object:
    """Crea el humano base MPFB2 (malla MakeHuman real, ver mpfb2-api-discovery.md)."""
    _remove_default_cube()
    result = bpy.ops.mpfb.create_human()
    if result != {'FINISHED'}:
        msg = f'mpfb.create_human fallo: {result}'
        raise RuntimeError(msg)
    return bpy.context.object


def _setup_preview_camera(
    target: bpy.types.Object,
    *,
    view: str,
) -> bpy.types.Object:
    # El humano MPFB2 mide ~1.66m, pies en z=0 — encuadrar el centro
    # vertical real (mitad de la altura), no target.location.z (que es
    # 0, el origin del objeto a la altura de los pies).
    mid_height = target.dimensions.z / 2

    camera_data = bpy.data.cameras.new(f'preview_{view}')
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = target.dimensions.z * 1.3
    camera = bpy.data.objects.new(f'preview_{view}', camera_data)
    bpy.context.collection.objects.link(camera)

    if view == 'front':
        camera.location = (0, -4, mid_height)
        camera.rotation_euler = (1.5708, 0, 0)
    else:  # side
        camera.location = (4, 0, mid_height)
        camera.rotation_euler = (1.5708, 0, 1.5708)

    return camera


def _render_preview(camera: bpy.types.Object, output_path: str) -> None:
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.filepath = output_path
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    bpy.ops.render.render(write_still=True)


def main() -> None:
    args = parse_args()
    output = args['output']
    preview_dir = args.get('preview_dir')

    target = _create_base_mesh()

    if preview_dir:
        for view in ('front', 'side'):
            camera = _setup_preview_camera(target, view=view)
            _render_preview(
                camera,
                f'{preview_dir.rstrip("/")}/mesh-preview-{view}.png',
            )

    bpy.ops.wm.save_as_mainfile(filepath=output)
    print(f'Malla guardada en {output}')


if __name__ == '__main__':
    main()
