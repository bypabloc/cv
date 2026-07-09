"""Pipeline Blender headless: cuerpo (FBX de Mixamo, o VRM/GLB, rig
mixamorig:*, cara pintada) + clips de Mixamo (FBX, rig mixamorig:*) -> UN GLB
con el cuerpo y todas las animaciones renombradas al esquema del journey.

Uso:
  blender --background --python build-character.py -- \
    <cuerpo.fbx|.vrm|.glb> <anims_dir> <salida.glb> [--anims a,b,c]

  <cuerpo>     : avatar con rig mixamorig:* (Mixamo Character FBX, VRoid, etc.)
  <anims_dir>  : carpeta con los FBX de Mixamo. El nombre de archivo (sin .fbx)
                 es el nombre del clip resultante (idle -> Idle, sit_down_desk
                 -> SitDownDesk). --anims limita a un subconjunto por nombre.
  <salida.glb> : GLB final (sin Draco; se comprime luego con gltf-transform).

CLAVE TÉCNICA (Mixamo -> cuerpo del otro pack):
- El cuerpo y Mixamo comparten el rig `mixamorig:*` -> las acciones se aplican
  al armature del cuerpo SIN retarget. Se importa cada FBX, se toma su Action,
  se agrega como track NLA del armature del cuerpo. glTF exporta cada track
  como un AnimationClip.
- ESCALA: los FBX de Mixamo vienen en cm con el armature escalado a 0.01. Se
  aplica esa escala al importar (transform_apply) para que la Action quede en
  la escala del cuerpo (metros).
- ROOT MOTION: los clips de locomoción/idle deben quedar IN-PLACE (el journey
  mueve la posición por código). Se ANCLA el canal de traslación XZ del hueso
  Hips en esos clips (los de la lista ROOT_LOCK). El descenso Y del sit SÍ se
  conserva (es lo que lo hace "sentado").
"""

import os
import re
import sys

import bpy

# clips donde el Hips NO debe trasladarse en XZ (in-place). El resto conserva
# su root motion tal cual (sit baja en Y y eso se respeta).
ROOT_LOCK_XZ = {
    'Idle',
    'Walk',
    'Run',
    'PanicRun',
    'KarateIdle',
    'RelaxedIdle',
    'InjuredIdle',
    'NervousWait',
}

# Mixamo prefija cada personaje/clip con un numero distinto (mixamorig12:Hips,
# mixamorig:Hips, ...). Ademas el ':' en el nombre del hueso rompe el matching
# de tracks de Three.js (GLTFLoader sanea el nodo a "mixamorig12Hips" pero el
# AnimationClip conserva "mixamorig12:Hips" -> el track no encuentra el nodo,
# el cuerpo queda en T-pose). Se normaliza TODO hueso a "mixamorig_<Nombre>":
# unifica el rig del cuerpo con el de cada clip (retarget por nombre) y elimina
# el ':'. El regex captura el prefijo mixamorig[digitos]?[:] o mixamorig[:].
_RIG_RE = re.compile(r'^mixamorig\d*[:_]?')
RIG_PREFIX = 'mixamorig_'


def normalize_bone_name(name: str) -> str:
    """mixamorig12:Hips -> mixamorig_Hips ; mixamorig:LeftArm -> mixamorig_LeftArm."""
    return RIG_PREFIX + _RIG_RE.sub('', name)


def normalize_armature_bones(arm: bpy.types.Object) -> None:
    """Renombra los huesos del armature al prefijo estable sin ':'."""
    for bone in arm.data.bones:
        bone.name = normalize_bone_name(bone.name)


def normalize_action_paths(action: bpy.types.Action) -> None:
    """Reescribe los data_path de la Action al nombre de hueso normalizado, para
    que targeteen los huesos renombrados del cuerpo (retarget + sin ':')."""
    for fc in action.fcurves:
        dp = fc.data_path
        if 'pose.bones["' in dp:
            old = dp.split('"')[1]
            new = normalize_bone_name(old)
            fc.data_path = dp.replace(f'"{old}"', f'"{new}"', 1)


def log(*a: object) -> None:
    print('[build-character]', *a, flush=True)


def to_clip_name(fname: str) -> str:
    """idle -> Idle ; sit_down_desk -> SitDownDesk ; walk_variant_1 -> WalkVariant1."""
    return ''.join(part.capitalize() for part in fname.split('_'))


def find_armature() -> bpy.types.Object | None:
    return next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)


# sockets del Principled BSDF cuya textura el MeshToonMaterial SI usa (color
# base). Cualquier TEX_IMAGE que alcance OTRO socket (Normal via Normal Map,
# Specular, Roughness, Metallic, ...) se descarta.
_KEEP_SOCKETS = {'Base Color'}


def _reaches_socket(node: bpy.types.Node, socket_names: set[str]) -> bool:
    """True si la salida de `node` llega (directa o via nodos intermedios como
    Normal Map / Separate Color) a alguno de los sockets nombrados del BSDF."""
    seen: set[str] = set()
    stack = [node]
    while stack:
        cur = stack.pop()
        if cur.name in seen:
            continue
        seen.add(cur.name)
        for out in cur.outputs:
            for link in out.links:
                dst = link.to_node
                if dst.type == 'BSDF_PRINCIPLED':
                    if link.to_socket.name in socket_names:
                        return True
                else:
                    stack.append(dst)
    return False


def strip_pbr_textures() -> None:
    """Deja SOLO la textura de color base en cada material (el journey usa
    MeshToonMaterial que solo lee `map`). Detecta el ROL de cada TEX_IMAGE por
    el socket del BSDF al que llega: conserva la que alcanza 'Base Color' y
    borra el resto (Normal/Specular/Roughness/Metallic) — la mayor parte del
    peso del GLB. Nombres de imagen Mixamo son genericos (file1, file3...), por
    eso se detecta por conexion, no por nombre."""
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        nt = mat.node_tree
        for node in list(nt.nodes):
            if node.type != 'TEX_IMAGE' or not node.image:
                continue
            if not _reaches_socket(node, _KEEP_SOCKETS):
                nt.nodes.remove(node)


# FBX de Mixamo: se importa en escala NATIVA (el importer deja el armature a
# scale 0.01 y la malla en cm). NO se escala en el pipeline ni en Three.js: al
# exportar el glTF, Blender aplica la escala del nodo armature y el modelo
# queda a ~1.77 m con el bind pose intacto (probado en el journey). Cuerpo y
# Actions comparten el mismo espacio -> coinciden por construccion.
_FBX_GLOBAL_SCALE = 1.0


def import_body(body_path: str) -> bpy.types.Object:
    """Importa el cuerpo (FBX de Mixamo, o VRM/GLB) escalado a metros y
    devuelve su armature (a scale 1, cuerpo ~1.7 m)."""
    low = body_path.lower()
    if low.endswith('.fbx'):
        bpy.ops.import_scene.fbx(
            filepath=body_path,
            ignore_leaf_bones=True,
            global_scale=_FBX_GLOBAL_SCALE,
        )
    else:
        glb = body_path
        if low.endswith('.vrm'):
            glb = body_path + '.glb'
            if not os.path.exists(glb):
                import shutil

                shutil.copy(body_path, glb)
        bpy.ops.import_scene.gltf(filepath=glb)
    arm = find_armature()
    if arm is None:
        msg = f'el cuerpo {body_path} no trae armature'
        raise RuntimeError(msg)
    arm.name = 'Body'
    # el FBX del cuerpo trae una Action basura (T-pose "mixamo.com|Layer0" de
    # 1-2 frames). Se elimina para que no salga como clip en el GLB.
    if arm.animation_data and arm.animation_data.action:
        junk = arm.animation_data.action
        arm.animation_data.action = None
        bpy.data.actions.remove(junk)
    # normalizar los nombres de hueso (mixamorig12:Hips -> mixamorig_Hips): las
    # Actions luego se normalizan al mismo esquema y targetean estos huesos.
    normalize_armature_bones(arm)
    return arm


def extract_action(fbx_path: str, clip_name: str) -> bpy.types.Action | None:
    """Importa un FBX de Mixamo (mismo global_scale que el cuerpo), ancla root
    motion si aplica, y devuelve la Action. Limpia los objetos importados."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(
        filepath=fbx_path,
        ignore_leaf_bones=True,
        global_scale=_FBX_GLOBAL_SCALE,
    )
    new = [o for o in bpy.data.objects if o not in before]
    arm = next((o for o in new if o.type == 'ARMATURE'), None)
    action = None
    if arm and arm.animation_data and arm.animation_data.action:
        action = arm.animation_data.action
        # normalizar los targets al mismo esquema que el cuerpo (retarget por
        # nombre + sin ':') ANTES de anclar el root o renombrar la Action.
        normalize_action_paths(action)
        if clip_name in ROOT_LOCK_XZ:
            _lock_root_xz(action)
        decimate_action(action)
        action.name = clip_name
        action.use_fake_user = True
        # desligar la Action del armature del FBX antes de borrarlo, si no
        # Blender la elimina junto con el objeto.
        arm.animation_data.action = None
    # borrar los objetos del FBX (ya tenemos la Action)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    return action


# los FBX de Mixamo son 60 fps sin keyframe reduction -> son el mayor peso del
# GLB. Se deja 1 keyframe de cada KEEP_EVERY (~20 fps efectivos): imperceptible
# en los clips del journey (idle/walk/sit/talk lentos) y ~3x menos peso.
_KEEP_EVERY = 3


def decimate_action(action: bpy.types.Action) -> None:
    """Sub-samplea cada fcurve a ~1/KEEP_EVERY de sus keyframes (conservando
    primero y ultimo), para bajar el peso del GLB. Deja el movimiento intacto a
    la escala temporal del journey."""
    for fc in action.fcurves:
        pts = fc.keyframe_points
        n = len(pts)
        if n <= 3:
            continue
        # indices a BORRAR (los que no caen en el paso ni son extremos)
        remove = [
            i for i in range(1, n - 1) if i % _KEEP_EVERY != 0
        ]
        for i in reversed(remove):
            pts.remove(pts[i], fast=True)
        fc.update()


def _lock_root_xz(action: bpy.types.Action) -> None:
    """Ancla SOLO el eje de AVANCE (Z) de la traslación de mixamorig_Hips,
    dejando libres el sway lateral (X) y el bob vertical (Y). Medido
    empíricamente en los FBX de Mixamo tras import en Blender: en
    `pose.bones["mixamorig_Hips"].location` el avance/root motion es el
    array_index 2 (Z-forward), el sway lateral es el 0 (X) y el vertical el 1
    (Y). El sistema mueve al NPC por código (in-place en Z), pero conservar el
    sway lateral X + el bob Y le da al caminar su balanceo natural (evita el
    andar rígido/robótico que se leía como 'malandro' al anclar X). Solo se
    congela Z. (Se llama tras normalize_action_paths, nombre ya normalizado.)"""
    path = 'pose.bones["mixamorig_Hips"].location'
    for fc in action.fcurves:
        if fc.data_path != path:
            continue
        if fc.array_index == 2:  # solo Z (avance) -> in-place; X/Y libres
            base = fc.keyframe_points[0].co[1] if fc.keyframe_points else 0.0
            for kp in fc.keyframe_points:
                kp.co[1] = base
                kp.handle_left[1] = base
                kp.handle_right[1] = base
            fc.update()


def main() -> int:
    argv = sys.argv[sys.argv.index('--') + 1:]
    if len(argv) < 3:
        log('args: <cuerpo> <anims_dir> <salida.glb> [--anims a,b,c]')
        return 2
    body_path, anims_dir, out_path = argv[0], argv[1], argv[2]
    only: set[str] | None = None
    if '--anims' in argv:
        only = set(argv[argv.index('--anims') + 1].split(','))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    body_arm = import_body(body_path)
    log(f'cuerpo importado, armature={body_arm.name}')

    fbxs = sorted(
        f for f in os.listdir(anims_dir) if f.lower().endswith('.fbx')
    )
    clips: list[bpy.types.Action] = []
    for fbx in fbxs:
        stem = fbx[:-4]
        if only is not None and stem not in only:
            continue
        clip_name = to_clip_name(stem)
        action = extract_action(os.path.join(anims_dir, fbx), clip_name)
        if action is None:
            log(f'{fbx} sin accion, omito')
            continue
        clips.append(action)
        log(f'clip {clip_name} <- {fbx}')

    if not clips:
        log('ADVERTENCIA: cero clips, el GLB saldra sin animaciones')

    # dejar solo la textura de color base (el toon material no usa normal/spec)
    strip_pbr_textures()

    # cada accion como track NLA del armature del cuerpo -> glTF exporta todas
    body_arm.animation_data_create()
    for action in clips:
        track = body_arm.animation_data.nla_tracks.new()
        track.name = action.name
        track.strips.new(action.name, int(action.frame_range[0]), action)

    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        export_yup=True,
        export_animations=True,
        export_animation_mode='ACTIONS',
        export_nla_strips=True,
        export_skins=True,
    )
    size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    log(f'EXPORTED {out_path} {size} bytes, {len(clips)} clips')
    return 0


if __name__ == '__main__':
    sys.exit(main())
