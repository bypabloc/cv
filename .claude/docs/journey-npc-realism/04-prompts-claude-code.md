# Prompts para Claude Code (Opus 4.8 / Sonnet 5)

> [Indice](README.md) | Anterior: [painterly + generadores IA](03-painterly-shading-y-generadores-ia.md)

Claude no genera geometría/imágenes 3D directamente, pero SÍ escribe y
ejecuta los scripts `bpy` vía su tool Bash, y puede **ver** los renders
(PNG) con su tool de lectura de imágenes para iterar sin que un humano
abra la GUI de Blender.

## Patrón de iteración

```text
escribir script → correr Blender headless → renderizar PNG
  → Claude lee el PNG → ajusta el script → re-renderiza → repetir
```

## Prompts de ejemplo

**1 — descubrir el API de MPFB2 (spike obligatorio primero)**:

> Instala el addon MPFB2 (zip en `devtools/npc_pipeline/vendor/mpfb2.zip`)
> en un Blender headless y explorá el API real que expone
> (`dir(bpy.ops.mpfb)`, filtrar `bpy.types` por `mpfb`). Documentá los
> operators disponibles para crear una malla humanoide base en
> `docs/specs/journey-npc-realism/mpfb2-api-discovery.md` antes de
> escribir ningún script de generación.

**2 — generar la malla + iterar sobre la silueta**:

> Con el API de MPFB2 ya documentado, escribí
> `devtools/npc_pipeline/scripts/generate_mesh.py`: un script bpy que
> cree una malla humanoide con proporciones neutras (altura ~1.7m), la
> guarde en `apps/journey-realistic/blender/assets/npc-base.blend`, y
> renderice vista frontal + lateral a PNG en `tmp/npc-pipeline/` con
> cámara ortográfica. Corré el script headless, después leé ambos PNG y
> decime si la silueta se ve anatómicamente razonable o si hay que
> ajustar proporciones — iterá hasta que se vea bien.

**3 — riggear y validar deformación**:

> Escribí `devtools/npc_pipeline/scripts/rig_mesh.py`: cargá
> `npc-base.blend`, agregá un Human (Meta-Rig) de Rigify, ajustá sus
> huesos a las proporciones de la malla (snap a tobillos/rodillas/
> caderas/hombros/muñecas/base del cuello), corré
> `bpy.ops.pose.rigify_generate()`, y aplicá parent automático con pesos
> por envolvente. Guardá `npc-rigged.blend` y renderizá una pose de
> prueba (brazo levantado) a PNG para que yo verifique que la piel se
> deforma sin artefactos antes de seguir con la animación.

**4 — exportar y cargar en Three.js**:

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

**5 — medir performance real**:

> En la escena de prueba con el NPC cargado, agregá una lectura de
> `renderer.info.render.calls`, `renderer.info.render.triangles` y el
> tamaño en disco del `.glb`. Corré esa escena headless con Playwright
> (desktop + user-agent móvil emulado), capturá los 3 números en ambos
> casos, y documentalos proponiendo un presupuesto de draw calls/sala
> para esta app.

## Por qué no un servidor MCP (`claude-blender`)

Existe un puente MCP comunitario (`claude-blender`) que expone `bpy` vía
JSON-RPC, pero es un proyecto de baja actividad y madurez no verificada
para producción (ver
[03-painterly-shading-y-generadores-ia.md](03-painterly-shading-y-generadores-ia.md)).
La ruta recomendada — y la que asumen los 5 prompts de arriba — es que
Claude Code escriba el script `.py` con Write/Edit y lo corra con
`blender --background --python <script> -- <args>` vía Bash, sin pasar
por ningún MCP intermedio.
