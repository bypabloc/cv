# Spike T4: API real de MPFB2 (descubierto corriendo Blender real)

> Corrido con Blender 4.2.22 LTS (portable, sin instalación de sistema) +
> MPFB2 v2.0.16 instalado desde el link directo de
> `extensions.blender.org` (sin cuenta). Resultado del spike obligatorio
> antes de escribir la lógica real de `generate_mesh.py`.

## Instalación: MPFB2 es una EXTENSION, no un addon legacy

El zip de MPFB2 trae `blender_manifest.toml` en la raíz (formato de
extensión de Blender 4.2+), **no** el formato legacy de addon
(`__init__.py` dentro de una carpeta con nombre del módulo). Por eso
`bpy.ops.preferences.addon_install()` falla con
`"ZIP packaged incorrectly; __init__.py should be in a directory, not at top-level"`.

La instalación correcta usa el API de extensiones:

```python
result = bpy.ops.extensions.package_install_files(
    filepath='devtools/npc_pipeline/vendor/mpfb2.zip',
    repo='user_default',   # repo local, sin remote_url — sin cuenta
    enable_on_install=True,
)
# result == {'FINISHED'}
```

El módulo Python queda namespaced como `bl_ext.user_default.mpfb` (NO
`mpfb` a secas) — pero los **operators** (`bpy.ops.mpfb.*`) SÍ quedan
bajo el namespace `mpfb` normal, porque el `bl_idname` de cada operator
lo define la clase misma, independiente de cómo se importó el módulo.

## `bpy.ops.mpfb` — 137 operators disponibles

Los relevantes para este pipeline:

| Operator | Qué hace |
|---|---|
| `create_human()` | Crea un humano MakeHuman con phenotype default. **Sin parámetros** (ajustables después via el modeling panel/properties). Confirmado: crea un objeto `Human` (MESH) con **19158 vértices** — la topología MakeHuman real, no un placeholder. |
| `human_from_presets(...)` | Crear desde un preset guardado (no usado en Etapa 1) |
| `add_rigify_rig()` | **Un solo operator que hace TODO**: crea el metarig de Rigify ajustado a las proporciones del humano activo, lo genera (equivalente a `bpy.ops.pose.rigify_generate()`), Y parentea + skinnea la malla al rig resultante con pesos reales — confirmado corriendo el pipeline completo: 333 vertex groups + modifier Armature en la malla, 930 huesos en el rig generado. `rig_mesh.py` final NO llama a `generate_rigify_rig()` por separado — un solo `add_rigify_rig()` alcanza. |
| `generate_rigify_rig()` | Genera el rig final desde un metarig YA EXISTENTE (equivalente MPFB2 de `bpy.ops.pose.rigify_generate()`) — solo hace falta si se agrega el metarig por separado; `add_rigify_rig()` ya lo incluye. |
| `convert_to_rigify()` | Flujo LEGACY (doc del operator: *"new characters should use the modern Add rigify metarig + Generate flow on the Rigging panel"*) — NO USAR, es el flujo viejo |
| `load_animation` / `save_animation` / `load_pose` / `save_pose` | Manejo de animaciones/poses propio de MPFB2 |
| `map_mixamo` | Mapeo a rigs Mixamo — **no aplica** (proyecto excluye Mixamo) |

## Correcciones al plan original

1. **NO** se necesita `bpy.ops.object.armature_human_metarig_add()` +
   snap manual de huesos (lo que decía el placeholder de `rig_mesh.py`):
   MPFB2 expone `add_rigify_rig()` que hace metarig + generate + parent +
   skin EN UN SOLO operator, ajustado al humano activo. Esto es MEJOR que
   el plan original — sin trabajo manual de posicionamiento de huesos ni
   una segunda llamada a `generate_rigify_rig()`.
2. El objeto default `Cube` de la escena de Blender debe borrarse antes
   de guardar (viene del escenario de arranque, no del humano MPFB2).
3. `create_human()` no tiene parámetros — la variación entre NPCs
   (distinto físico/pelo/piel) se logra ajustando propiedades del
   modeling panel DESPUÉS de crear el humano (properties de MPFB2,
   pendiente de explorar si se necesita variedad entre los ~40-50 NPCs;
   fuera del scope de esta primera pasada end-to-end).

## Animación (T7): 4 bugs descubiertos corriendo el pipeline real

`animate.py` genera 2 clips (`idle`, `walk`) con keyframes FK. Cuatro
hallazgos que el plan original no anticipaba:

1. **El rig generado por `add_rigify_rig()` queda en modo IK, no FK.**
   Cada brazo/pierna tiene un custom property `IK_FK` en su bone
   `*_parent.<L|R>` (`thigh_parent.L/R`, `upper_arm_parent.L/R`):
   `0.0` = IK (default), `1.0` = FK. Rotar `thigh_fk`/`upper_arm_fk`
   directamente NO mueve la malla mientras el rig este en modo IK —
   confirmado renderizando (rotar `upper_arm_fk.L` 80° no cambiaba nada
   hasta forzar `IK_FK = 1.0`). `_force_fk_mode()` en `animate.py` lo
   hace antes de keyframear.
2. **Signo de rotación confirmado renderizando**: en `thigh_fk.<side>`,
   X positivo = pierna hacia ATRÁS, X negativo = pierna hacia ADELANTE.
3. **El exportador glTF (`export_animation_mode='ACTIONS'`) SOLO incluye
   la acción activa de cada objeto MÁS las que estén en NLA tracks** —
   una acción creada y luego reemplazada por otra (aunque tenga
   `use_fake_user=True`) NO se exporta. Con solo `fake_user`, el clip
   `idle` faltaba del `.glb` final (solo aparecía `walk`, la última
   acción activa). Fix: `_push_to_nla()` empuja cada acción a su propio
   NLA track (`rig.animation_data.nla_tracks.new()` +
   `track.strips.new(...)`) inmediatamente después de crearla.
4. **El clip glTF final se nombra igual al NLA TRACK, no a la acción
   Blender.** Con `track.name = f'{action.name}_track'` el `.glb` traía
   animaciones `idle_track`/`walk_track` en vez de `idle`/`walk` —
   descubierto inspeccionando con `gltf-transform inspect`. Fix: el track
   se nombra IGUAL que la acción (`track.name = action.name`), sin
   sufijo — `npc-gltf-loader.ts` matchea `clip.name` como
   `CharacterPose` exacto.

## Blender headless: `--python-exit-code` es OBLIGATORIO

Por defecto, `blender --background --python script.py` imprime el
traceback de una excepción Python sin capturar pero **sigue saliendo con
exit code 0** — confirmado corriendo un script con un bug real: el
traceback aparecía en stdout pero `devtools`'s `run_blender_script()`
(que solo chequea `returncode != 0`) trataba el fallo como éxito. Fix en
`blender_runner.build_blender_command()`: agregar
`'--python-exit-code', '1'` al argv — con esto, una excepción Python no
capturada hace que Blender salga con code 1 (o el que se pase), y
`devtools` lo detecta correctamente.

## Three.js: `OutlinePass` compone el contorno con `AdditiveBlending`

Confirmado leyendo `three/examples/jsm/postprocessing/OutlinePass.js`
(r0.170): el paso final de composición (`getOverlayMaterial()`) usa
`blending: AdditiveBlending`. Un color de contorno casi negro (`#141018`,
el ink manga del resto de la sala) es **invisible** con additive
blending sin importar `edgeStrength` — additive solo puede ACLARAR un
píxel, nunca oscurecerlo. Confirmado renderizando: `edgeStrength=10` +
`#141018` no mostraba NADA; con un color claro (`#f5f2ea`) el contorno
aparece correctamente durante la animación (sin artefactos de skinning,
AC-7 cumplido). **OutlinePass sirve para un contorno tipo "glow" de
selección, NO para replicar el ink oscuro manga de `toon.ts`** — un
contorno oscuro real requeriría un shader de silueta propio (Etapa 2,
fuera de este plan).

## Siguiente paso

Ninguno pendiente para Etapa 1 — el pipeline completo
(generate-mesh → rig → animate → export) corre end-to-end y el resultado
se verificó visualmente en `apps/journey-realistic` (ver
`09-verificacion-e2e.md`).
