"""Blender headless: keyframe basic idle/walk actions on the Rigify rig.

Run via devtools:
  python devtools/run.py npc_pipeline animate \
    --input=<npc-rigged.blend> --output=<npc-animated.blend>

Direct invocation:
  blender --background --python animate.py -- \
    --input=<X> --output=<Y>

Etapa 1 cubre 2 clips minimos (nombrados igual que ``CharacterPose`` en
``character.ts`` para que Three.js los reconozca por nombre):

- ``idle``: bob sutil de cadera (2 keyframes, loop).
- ``walk``: ciclo de zancada de 4 keyframes sobre las piernas FK
  (``thigh_fk``/``shin_fk``) + contra-balanceo de brazos
  (``upper_arm_fk``), loop de 24 frames (1s a 24fps).

Ambos requieren forzar modo FK (``IK_FK = 1.0``) en los bones parent de
pierna/brazo — por defecto el rig generado por
``bpy.ops.mpfb.add_rigify_rig()`` queda en modo IK (confirmado
corriendo el pipeline real: rotar los bones FK en modo IK no mueve la
malla).

``talk``/``sit``/``kneel``/``fight``/``wave`` (resto de ``CharacterPose``)
quedan para una pasada siguiente — no bloquean la Etapa 1 (silueta +
animacion basica).
"""

import math
from pathlib import Path
import sys

import bpy


sys.path.insert(0, str(Path(__file__).resolve().parent))
from _argv import parse_args


def _find_rig() -> bpy.types.Object:
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE' and obj.name.endswith('.rigify'):
            return obj
    msg = "No se encontro ningun armature '*.rigify' en el .blend de entrada"
    raise RuntimeError(msg)


def _force_fk_mode(rig: bpy.types.Object) -> None:
    for side in ('L', 'R'):
        rig.pose.bones[f'thigh_parent.{side}']['IK_FK'] = 1.0
        rig.pose.bones[f'upper_arm_parent.{side}']['IK_FK'] = 1.0


def _new_action(rig: bpy.types.Object, name: str) -> bpy.types.Action:
    action = bpy.data.actions.new(name=name)
    # fake_user=True es OBLIGATORIO: sin el, la accion que NO queda activa
    # al final (idle, reemplazada por walk en animation_data.action) tiene
    # 0 usuarios reales y el exportador glTF (export_animation_mode=
    # 'ACTIONS') la omite silenciosamente — descubierto corriendo el
    # pipeline real (glTF final solo traia 'walk', faltaba 'idle').
    action.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = action
    return action


def _keyframe_euler_x(
    rig: bpy.types.Object,
    bone_name: str,
    frame: int,
    degrees: float,
) -> None:
    bone = rig.pose.bones[bone_name]
    bone.rotation_mode = 'XYZ'
    bone.rotation_euler = (math.radians(degrees), 0, 0)
    bone.keyframe_insert(data_path='rotation_euler', frame=frame)


def _keyframe_location_z(
    rig: bpy.types.Object,
    bone_name: str,
    frame: int,
    z: float,
) -> None:
    bone = rig.pose.bones[bone_name]
    bone.location = (bone.location.x, bone.location.y, z)
    bone.keyframe_insert(data_path='location', frame=frame)


def _build_idle_action(rig: bpy.types.Object) -> bpy.types.Action:
    action = _new_action(rig, 'idle')
    hips = rig.pose.bones['hips']
    hips.location = (0, 0, 0)
    hips.keyframe_insert(data_path='location', frame=1)
    _keyframe_location_z(rig, 'hips', 13, 0.015)
    hips.location = (0, 0, 0)
    hips.keyframe_insert(data_path='location', frame=25)
    for fcurve in action.fcurves:
        fcurve.extrapolation = 'CONSTANT'
        for kp in fcurve.keyframe_points:
            kp.interpolation = 'SINE'
    return action


def _build_walk_action(rig: bpy.types.Object) -> bpy.types.Action:
    action = _new_action(rig, 'walk')

    # Signo confirmado renderizando: X positivo en thigh_fk.<side> = pierna
    # hacia ATRAS; X negativo = pierna hacia ADELANTE.
    stride = 35.0
    knee_lift = 45.0
    arm_swing = 25.0

    keyframes = [
        # frame, L thigh, R thigh, L shin, R shin, L arm, R arm
        (1, -stride, stride, 0, 0, arm_swing, -arm_swing),
        (7, 0, 0, 0, knee_lift, 0, 0),
        (13, stride, -stride, 0, 0, -arm_swing, arm_swing),
        (19, 0, 0, knee_lift, 0, 0, 0),
        (25, -stride, stride, 0, 0, arm_swing, -arm_swing),  # = frame 1 (loop)
    ]

    for frame, l_thigh, r_thigh, l_shin, r_shin, l_arm, r_arm in keyframes:
        _keyframe_euler_x(rig, 'thigh_fk.L', frame, l_thigh)
        _keyframe_euler_x(rig, 'thigh_fk.R', frame, r_thigh)
        _keyframe_euler_x(rig, 'shin_fk.L', frame, l_shin)
        _keyframe_euler_x(rig, 'shin_fk.R', frame, r_shin)
        _keyframe_euler_x(rig, 'upper_arm_fk.L', frame, l_arm)
        _keyframe_euler_x(rig, 'upper_arm_fk.R', frame, r_arm)

    for fcurve in action.fcurves:
        fcurve.extrapolation = 'CONSTANT'
        for kp in fcurve.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'

    return action


def _push_to_nla(rig: bpy.types.Object, action: bpy.types.Action) -> None:
    """Empuja la accion a su propio NLA track.

    ``export_animation_mode='ACTIONS'`` del exportador glTF SOLO incluye
    la accion activa de cada objeto MAS las que esten en NLA tracks — una
    accion creada y luego reemplazada por otra (fake_user o no) NO alcanza
    (descubierto corriendo el pipeline real: con solo fake_user, 'idle'
    seguia faltando del glTF final). Empujarlas a tracks separados
    garantiza que TODAS se exporten sin importar cual quede activa.

    El exportador nombra el clip glTF final segun el NLA TRACK, NO segun
    la accion (descubierto inspeccionando el .glb con gltf-transform: con
    ``track.name = f'{action.name}_track'`` el clip exportado se llamaba
    'idle_track'/'walk_track' en vez de 'idle'/'walk'). npc-gltf-loader.ts
    matchea ``clip.name`` como ``CharacterPose`` exacto ('idle', 'walk'),
    asi que el track debe llamarse igual que la accion, sin sufijo.
    """
    track = rig.animation_data.nla_tracks.new()
    track.name = action.name
    track.strips.new(action.name, 1, action)


def main() -> None:
    args = parse_args()
    input_path = args['input']
    output_path = args['output']

    bpy.ops.wm.open_mainfile(filepath=input_path)
    rig = _find_rig()
    _force_fk_mode(rig)

    idle_action = _build_idle_action(rig)
    rig.animation_data.action = None  # libera el slot antes de empujar a NLA
    _push_to_nla(rig, idle_action)

    walk_action = _build_walk_action(rig)
    rig.animation_data.action = None
    _push_to_nla(rig, walk_action)

    print(
        f'Accion creada: {idle_action.name} ({len(idle_action.fcurves)} fcurves)'
    )
    print(
        f'Accion creada: {walk_action.name} ({len(walk_action.fcurves)} fcurves)'
    )

    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f'Animaciones guardadas en {output_path}')


if __name__ == '__main__':
    main()
