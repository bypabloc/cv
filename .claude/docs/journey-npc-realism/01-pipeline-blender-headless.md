# Pipeline Blender headless: malla, rig, animación

> [Indice](README.md) | Siguiente: [export + Three.js](02-export-y-threejs-integracion.md)
>
> Verificado corriendo el pipeline real end-to-end (2026-07-07) con
> Blender 4.2.22 LTS portable + MPFB2 v2.0.16. Reemplaza la version
> teorica original — cada paso de abajo es lo que REALMENTE funciona,
> no lo que el research asumia antes de correrlo. Detalle de cada
> hallazgo: `docs/specs/journey-npc-realism/mpfb2-api-discovery.md`.

## Setup (una sola vez por máquina)

Requiere Blender >=4.2 instalado localmente (no es dependencia del
monorepo — es un binario del sistema del desarrollador). Si no hay
permisos de instalación a nivel de sistema (sin `sudo`), el build
**portable** de blender.org sirve igual (tar.xz, sin instalador):

```bash
# Portable, sin root:
curl -fsSL -o blender.tar.xz \
  https://download.blender.org/release/Blender4.2/blender-4.2.22-linux-x64.tar.xz
tar xf blender.tar.xz
./blender-4.2.22-linux-x64/blender --version   # Blender 4.2.22 LTS
```

Todos los comandos `npc_pipeline` de abajo aceptan `--blender-bin=<ruta>`
para apuntar a un binario portable en vez de depender de `PATH`.

## MPFB2 es una EXTENSION (Blender 4.2+), NO un addon legacy

El zip de MPFB2 (descargado sin cuenta desde `extensions.blender.org`)
trae `blender_manifest.toml` en la raíz — formato de **Extension**, no
el legacy `__init__.py`-en-carpeta. Por eso
`bpy.ops.preferences.addon_install()` FALLA con
`"ZIP packaged incorrectly; __init__.py should be in a directory"`. La
instalación correcta:

```python
result = bpy.ops.extensions.package_install_files(
    filepath='devtools/npc_pipeline/vendor/mpfb2.zip',
    repo='user_default',   # repo local, SIN remote_url — sin cuenta
    enable_on_install=True,
)
# result == {'FINISHED'}
```

El módulo Python queda namespaced `bl_ext.user_default.mpfb`, pero los
**operators** (`bpy.ops.mpfb.*`) SIGUEN bajo el namespace `mpfb` normal
(el `bl_idname` lo define la clase, no el path de import). Rigify viene
bundled con Blender — solo hace falta `bpy.ops.preferences.addon_enable(
module='rigify')`.

Comando devtools:

```bash
python devtools/run.py npc_pipeline install-addons \
  --mpfb2-zip=devtools/npc_pipeline/vendor/mpfb2.zip \
  --blender-bin=<ruta-a-blender>
```

## Generar la malla base humanoide (MPFB2)

`bpy.ops.mpfb.create_human()` — **sin parámetros** — crea un objeto
`Human` (MESH) con la topología MakeHuman real: **19158 vértices**,
~1.66m de altura, pies en `z=0`. El objeto `Cube` default de la escena
de arranque de Blender se borra antes (no es parte del humano).

```bash
python devtools/run.py npc_pipeline generate-mesh \
  --output=apps/journey-realistic/blender/assets/npc-base.blend \
  --preview-dir=tmp/npc-pipeline/ \
  --blender-bin=<ruta-a-blender>
```

Produce el `.blend` + 2 renders de verificación (frontal + lateral,
cámara ortográfica, EEVEE Next) a PNG — encuadrar por
`target.dimensions.z` (la altura real del humano), NO por
`target.location.z` (que es 0, el origen a la altura de los pies).

## Riggear con Rigify — UN SOLO operator

MPFB2 expone `bpy.ops.mpfb.add_rigify_rig()`, que hace TODO en un paso:
crea el metarig de Rigify ajustado a las proporciones del humano activo,
lo genera (equivalente a `bpy.ops.pose.rigify_generate()`), y parentea +
skinnea la malla con pesos reales. Confirmado: 333 vertex groups +
modifier Armature en la malla, 930 huesos en el rig generado.

```python
human = bpy.data.objects['Human']
bpy.context.view_layer.objects.active = human
bpy.ops.object.select_all(action='DESELECT')
human.select_set(True)
bpy.ops.mpfb.add_rigify_rig()  # metarig + generate + parent + skin, TODO en uno
```

**NO** hace falta `armature_human_metarig_add()` manual, snap de huesos
a mano, ni una llamada separada a `generate_rigify_rig()`.

```bash
python devtools/run.py npc_pipeline rig \
  --input=apps/journey-realistic/blender/assets/npc-base.blend \
  --output=apps/journey-realistic/blender/assets/npc-rigged.blend \
  --blender-bin=<ruta-a-blender>
```

Validar renderizando una pose de prueba: mover el hueso IK
`hand_ik.L` (NO `upper_arm_fk.L` — ver siguiente sección) confirma
deformación correcta sin artefactos de piel rota.

## Animación: el rig nace en modo IK, hay que forzar FK

Los clips (`idle`, `walk` — Etapa 1 solo cubre estos dos; `talk`/`sit`/
`kneel`/`fight`/`wave` quedan para una pasada siguiente) se crean **una
sola vez** por keyframing directo sobre los huesos FK, reutilizados en
todas las instancias sin retargeting per-NPC.

**Hallazgo clave**: el rig que genera `add_rigify_rig()` queda en modo
**IK** por defecto — rotar `thigh_fk.<L|R>` / `upper_arm_fk.<L|R>`
directamente NO mueve la malla (confirmado: rotar `upper_arm_fk.L` 80°
no cambió nada en el render hasta forzar FK). Cada brazo/pierna tiene un
custom property `IK_FK` en su bone `*_parent.<L|R>`:

```python
rig.pose.bones['thigh_parent.L']['IK_FK'] = 1.0       # 1.0 = FK
rig.pose.bones['thigh_parent.R']['IK_FK'] = 1.0
rig.pose.bones['upper_arm_parent.L']['IK_FK'] = 1.0
rig.pose.bones['upper_arm_parent.R']['IK_FK'] = 1.0
```

Con esto, `thigh_fk`/`shin_fk`/`upper_arm_fk` SÍ deforman la malla al
rotarlos. Signo confirmado renderizando: en `thigh_fk.<side>`, X
positivo = pierna hacia ATRÁS, X negativo = pierna hacia ADELANTE.

```bash
python devtools/run.py npc_pipeline animate \
  --input=apps/journey-realistic/blender/assets/npc-rigged.blend \
  --output=apps/journey-realistic/blender/assets/npc-animated.blend \
  --blender-bin=<ruta-a-blender>
```

## Exportar clips múltiples: hace falta NLA tracks, no solo `fake_user`

El exportador glTF nativo de Blender
(`export_animation_mode='ACTIONS'`) exporta **"actives and on NLA
tracks"** — solo la acción ACTIVA de cada objeto MÁS las que estén
empujadas a un NLA track. Marcar una acción con `use_fake_user = True`
**NO alcanza**: confirmado exportando con solo `fake_user` — el `.glb`
final traía únicamente `walk` (la última acción activa), `idle`
faltaba.

Fix: empujar cada acción a su propio NLA track inmediatamente después
de crearla:

```python
rig.animation_data_create()
rig.animation_data.action = idle_action
# ... keyframear idle ...
track = rig.animation_data.nla_tracks.new()
track.name = idle_action.name        # IGUAL al nombre de la accion, SIN sufijo
track.strips.new(idle_action.name, 1, idle_action)
rig.animation_data.action = None     # libera el slot antes de la siguiente
```

**El clip glTF final se nombra igual al NLA TRACK, no a la acción** —
si el track se llama `f'{action.name}_track'`, el `.glb` trae animaciones
`idle_track`/`walk_track` en vez de `idle`/`walk` (descubierto
inspeccionando con `gltf-transform inspect`). El nombre del track debe
ser EXACTAMENTE el de la acción para que `npc-gltf-loader.ts` (que
matchea `clip.name` como `CharacterPose`) los reconozca.

## Blender headless: `--python-exit-code` es obligatorio

Por defecto, `blender --background --python script.py` imprime el
traceback de una excepción sin capturar pero **sigue saliendo con exit
code 0** — un script que falla se reporta como éxito. El flag
`--python-exit-code <code>` (documentado en `blender --help`) hace que
Blender salga con ese código ante una excepción Python:

```bash
blender --background --python-exit-code 1 --python script.py -- <args>
```

`devtools/npc_pipeline/blender_runner.build_blender_command()` ya lo
agrega siempre — no hace falta pasarlo a mano en los comandos
`npc_pipeline`.

## Anti-patrones

| Anti-patrón | Por qué | Corrección |
|-------------|---------|------------|
| `bpy.ops.preferences.addon_install()` para MPFB2 | MPFB2 v2.0.16 es una Extension (manifest), no un addon legacy | `bpy.ops.extensions.package_install_files(repo='user_default', enable_on_install=True)` |
| `armature_human_metarig_add()` + snap manual de huesos | `add_rigify_rig()` de MPFB2 ya hace metarig+generate+parent+skin en un paso | `bpy.ops.mpfb.add_rigify_rig()` sobre el objeto `Human` activo |
| Rotar `*_fk` bones esperando que deformen la malla | El rig nace en modo IK; los FK no tienen efecto hasta forzar el switch | `pose.bones['*_parent.<side>']['IK_FK'] = 1.0` antes de keyframear |
| Confiar en `use_fake_user=True` para exportar 2+ acciones | El exportador solo incluye la acción activa + las de NLA tracks | Empujar cada acción a su propio NLA track (`nla_tracks.new()` + `strips.new()`) |
| Nombrar el NLA track distinto a la acción (ej. `f'{name}_track'`) | El clip glTF final se llama como el TRACK, no la acción | `track.name = action.name`, sin sufijo |
| Correr Blender headless sin `--python-exit-code` | Blender sale 0 aunque el script Python haya lanzado una excepción | Siempre `--python-exit-code 1` (ya lo hace `blender_runner.py`) |
| Riggear con Mixamo | Requiere cuenta Adobe (viola la restricción "sin cuenta") | Rigify (incluido en Blender) via `add_rigify_rig()` |
