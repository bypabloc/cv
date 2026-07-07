# Pipeline Blender headless (Etapa 1) + prompts para Claude Code

> Todo este pipeline corre 100% local, sin cuenta, orquestado por el
> comando devtools nuevo `npc_pipeline` (ver
> [04-nueva-app-scaffold.md](04-nueva-app-scaffold.md)). Cada script real
> se ejecuta DENTRO de Blender (`bpy`), invocado por devtools vía
> subprocess — no requiere abrir la GUI.

## A. Tipos de archivo del pipeline end-to-end

| Etapa | Archivo | Formato | Contiene |
|-------|---------|---------|----------|
| Malla base | `npc-base.blend` | Blender nativo | Malla humanoide MPFB2, sin rig |
| Rig | `npc-rigged.blend` | Blender nativo | Malla + armature Rigify + skin weights (envelope/automatic) |
| Animación | (mismo `.blend`) | Acciones Blender (`bpy.types.Action`) | Clips `idle`, `walk`, `talk`, `sit` keyframeados sobre el rig |
| Export crudo | `npc-base.raw.glb` | glTF binario | Export directo del exportador nativo de Blender (sin comprimir) |
| Export final | `npc-base.glb` | glTF binario + `EXT_meshopt_compression` | Comprimido con glTF-Transform CLI — este es el que consume Three.js |
| Preview | `mesh-preview-*.png` | PNG | Renders de verificación (frontal/lateral/pose) para revisión humana o de Claude |

No hay mapas de textura en Etapa 1 (material toon/flat simple, sin
albedo/normal pintados — eso es Etapa 2).

## B. Workflow paso a paso

### Paso 0 — Setup (una sola vez)

```bash
# Blender >= 4.2 (requisito de MPFB2). Verificar version instalada:
blender --version

# Instalar el addon MPFB2 headless (zip descargado manualmente desde
# static.makehumancommunity.org, sin cuenta necesaria):
blender --background --python devtools/npc_pipeline/scripts/install_addons.py \
  -- --mpfb2-zip=devtools/npc_pipeline/vendor/mpfb2.zip
```

`install_addons.py` (esqueleto):

```python
import sys
import bpy

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
mpfb2_zip = next(
    (a.split('=', 1)[1] for a in argv if a.startswith('--mpfb2-zip=')), None,
)

if mpfb2_zip:
    bpy.ops.preferences.addon_install(filepath=mpfb2_zip)
    bpy.ops.preferences.addon_enable(module='mpfb')

# Rigify viene incluido en Blender: solo hace falta habilitarlo.
bpy.ops.preferences.addon_enable(module='rigify')
bpy.ops.wm.save_userpref()
```

**Spike obligatorio antes de seguir**: el API exacto de MPFB2
(`bpy.ops.mpfb.*`) no quedó verificado en el research (solo se confirmó
que el addon existe, es gratis y está mantenido). Primera tarea real:
correr `dir(bpy.ops.mpfb)` en la consola de Blender tras habilitar el
addon y documentar los operators disponibles en
`docs/specs/journey-npc-realism/mpfb2-api-discovery.md` ANTES de escribir
`generate_mesh.py`.

### Paso 1 — Generar la malla base humanoide (MPFB2)

```bash
blender --background --python devtools/npc_pipeline/scripts/generate_mesh.py \
  -- --output=apps/journey-realistic/blender/assets/npc-base.blend \
     --preview-dir=tmp/npc-pipeline/
```

Responsabilidades del script: crear la malla vía los operators MPFB2
descubiertos en el spike, con proporciones neutras (altura ~1.7m,
topología manifold sin n-gons rotos — AC-2), guardar el `.blend`, y
renderizar 2 vistas (frontal + lateral, cámara ortográfica, motor EEVEE)
a PNG para revisión.

### Paso 2 — Riggear con Rigify

```bash
blender --background --python devtools/npc_pipeline/scripts/rig_mesh.py \
  -- --input=apps/journey-realistic/blender/assets/npc-base.blend \
     --output=apps/journey-realistic/blender/assets/npc-rigged.blend
```

Flujo dentro del script (API de Rigify bien documentada, confianza
alta):

```python
import bpy

# 1. Agregar el metarig humano de Rigify (menu "Add Rigify > Human")
bpy.ops.object.armature_human_metarig_add()
metarig = bpy.context.object

# 2. Ajustar los huesos del metarig a las proporciones de la malla MPFB2
#    (snap manual/scripted a vertices clave: tobillos, rodillas, caderas,
#    hombros, munecas, base del cuello — tarea de la seccion 6 del plan).

# 3. Generar el rig final (operator real de Rigify, corre en Pose Mode
#    sobre el metarig)
bpy.ops.pose.rigify_generate()

# 4. Parent de la malla al rig generado con pesos automaticos
#    (bpy.ops.object.parent_set(type='ARMATURE_AUTO'))
```

Validación (AC-3): renderizar una pose de prueba (brazo levantado) y
confirmar visualmente que la piel se deforma sin artefactos antes de
seguir.

### Paso 3 — Animación (keyframing manual, sin Mixamo ni retargeting)

Como todos los NPCs comparten el MISMO rig base, los 4 clips
(`idle`, `walk`, `talk`, `sit` — mismos nombres que `CharacterPose` en
`character.ts`) se crean **una sola vez** sobre `npc-rigged.blend` por
keyframing manual en Blender (ciclo estándar de animación: pose clave
cada 0.3-0.5s, `Graph Editor` con interpolación `Bezier`/`Linear` según
el clip). No requiere ningún addon adicional.

**Opcional (spike, no bloqueante)**: si el keyframing manual resulta
lento, evaluar importar motion capture BVH de dominio público (ej. CMU
Mocap Database, `mocap.cs.cmu.edu`) con el add-on bundled de Blender
"Motion Capture (BVH) format" (`io_anim_bvh`, incluido en toda instalación
de Blender, solo requiere habilitarse — **no confundir con
`Motion-capture-connector`**, que es el addon de terceros cuya
compatibilidad con Rigify moderno no está verificada) y retargetear a
mano con constraints nativos (`Copy Rotation`/`Copy Location` + `Bake
Action`, ruta confirmada en el research).

### Paso 4 — Export a `.glb` (dos pasos: nativo + compresión)

```bash
# 4a. Export crudo con el exportador nativo de Blender (glTF2, incluido)
blender --background --python devtools/npc_pipeline/scripts/export_glb.py \
  -- --input=apps/journey-realistic/blender/assets/npc-rigged.blend \
     --output=tmp/npc-pipeline/npc-base.raw.glb

# 4b. Comprimir con glTF-Transform CLI (Meshopt: geometria + animacion)
npx --yes @gltf-transform/cli meshopt \
  tmp/npc-pipeline/npc-base.raw.glb \
  apps/journey-realistic/public/models/npc-base.glb
```

`export_glb.py` usa el operator nativo de Blender:

```python
bpy.ops.export_scene.gltf(
    filepath=output_path,
    export_format='GLB',
    export_animations=True,
    export_skins=True,
    export_apply=True,
)
```

## C. Prompts para Claude Code (Opus 4.8 / Sonnet 5)

Claude no genera geometría/imágenes 3D directamente, pero SÍ escribe y
ejecuta los scripts `bpy` vía su tool Bash, y puede **ver** los renders
(PNG) con su tool de lectura de imágenes para iterar sin que un humano
abra la GUI de Blender. Patrón: **escribir script → correr Blender
headless → renderizar PNG → Claude lee el PNG → ajusta el script →
re-renderiza**.

**Prompt 1 — descubrir el API de MPFB2 (spike obligatorio primero)**:

> Instala el addon MPFB2 (zip en `devtools/npc_pipeline/vendor/mpfb2.zip`)
> en un Blender headless y explorá el API real que expone
> (`dir(bpy.ops.mpfb)`, filtrar `bpy.types` por `mpfb`). Documentá los
> operators disponibles para crear una malla humanoide base en
> `docs/specs/journey-npc-realism/mpfb2-api-discovery.md` antes de
> escribir ningún script de generación.

**Prompt 2 — generar la malla + iterar sobre la silueta**:

> Con el API de MPFB2 ya documentado, escribí
> `devtools/npc_pipeline/scripts/generate_mesh.py`: un script bpy que
> cree una malla humanoide con proporciones neutras (altura ~1.7m), la
> guarde en `apps/journey-realistic/blender/assets/npc-base.blend`, y
> renderice vista frontal + lateral a PNG en `tmp/npc-pipeline/` con
> cámara ortográfica. Corré el script headless, después leé ambos PNG y
> decime si la silueta se ve anatómicamente razonable o si hay que
> ajustar proporciones — iterá hasta que se vea bien.

**Prompt 3 — riggear y validar deformación**:

> Escribí `devtools/npc_pipeline/scripts/rig_mesh.py`: cargá
> `npc-base.blend`, agregá un Human (Meta-Rig) de Rigify, ajustá sus
> huesos a las proporciones de la malla (snap a tobillos/rodillas/
> caderas/hombros/muñecas/base del cuello), corré
> `bpy.ops.pose.rigify_generate()`, y aplicá parent automático con pesos
> por envolvente. Guardá `npc-rigged.blend` y renderizá una pose de
> prueba (brazo levantado) a PNG para que yo verifique que la piel se
> deforma sin artefactos antes de seguir con la animación.

**Prompt 4 — exportar y cargar en Three.js**:

> Con `npc-rigged.blend` y sus 4 clips de animación ya creados, escribí
> `devtools/npc_pipeline/scripts/export_glb.py` (export nativo con
> `bpy.ops.export_scene.gltf`, `export_animations=True,
> export_skins=True`) y corré glTF-Transform CLI (`meshopt`) para
> comprimir el resultado a
> `apps/journey-realistic/public/models/npc-base.glb`. Después escribí
> un componente de prueba en `apps/journey-realistic/src/engine/` que
> cargue ese `.glb` con `GLTFLoader`, reproduzca el clip `walk` con
> `AnimationMixer`, y confirmame con un screenshot (Playwright) que la
> animación corre sin geometría rota.

**Prompt 5 — medir performance real (AC-8)**:

> En la escena de prueba con el NPC cargado, agregá una lectura de
> `renderer.info.render.calls`, `renderer.info.render.triangles` y el
> tamaño en disco del `.glb`. Corré esa escena headless con Playwright
> (desktop + user-agent móvil emulado), capturá los 3 números en ambos
> casos, y documentalos en
> `docs/specs/journey-npc-realism/09-verificacion-e2e.md` proponiendo un
> presupuesto de draw calls/sala para esta app.

## D. Generadores IA 3D locales — por qué NO se usan en Etapa 1

TripoSR, InstantMesh y Wonder3D tienen números de rendimiento reales y
verificados (velocidad, VRAM), pero sus claims de licencia permisiva +
"100% local sin cuenta" fueron refutadas en la verificación adversarial
del research (ver decisión 3 del README). Quedan fuera de este plan; si
en el futuro alguien quiere re-evaluarlos, el primer paso es releer a
mano el archivo `LICENSE` real de cada repo y confirmar si la descarga
de pesos preentrenados exige un token/cuenta de Hugging Face (posible
gated repo) — no asumir lo que dicen los abstracts/papers.
