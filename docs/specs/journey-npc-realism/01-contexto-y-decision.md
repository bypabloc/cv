# 1-5. Contexto, solución, AC y diagramas

## 1. Contexto / Problema

`apps/journey` (CV interactivo 3D, Three.js vanilla) puebla sus 10 salas
con ~40-50 NPCs generados por un único builder paramétrico
(`src/engine/character.ts`, 831 líneas): cada personaje es un ensamblado
de primitivas (`BoxGeometry`/`SphereGeometry`/`ConeGeometry`) fusionadas
con `BufferGeometryUtils.mergeGeometries`, con la cara pintada en un
`CanvasTexture` (ojos + parpadeo), material toon + contorno vía
inverted-hull (`src/engine/toon.ts`, 790 líneas), y poses (idle/walk/
fight/sit/kneel/wave/talk) hechas por transformaciones manuales de las
partes del cuerpo. **No hay skeleton/rig ni `SkinnedMesh`.**

El dueño del proyecto reporta que el resultado se ve "robótico y
horrible" y quiere subir el nivel de credibilidad anatómica, apuntando a
un estilo visual painterly (referencia: "Gato con Botas: El Último
Deseo" — la técnica de shading/textura, no los personajes puntuales de
la película).

### Hallazgos de exploración (research profundo, 2026-07-06)

Workflow `deep-research` (112 agentes, 6 ángulos de búsqueda, 29 fuentes
fetcheadas, 103 claims extraídas, 25 verificadas con voto adversarial
3-vías: 19 confirmadas, 6 refutadas). Resumen de lo que sobrevivió la
verificación:

- **MPFB2** (Makehuman Plugin For Blender) es un addon de Blender
  gratuito y open-source (GPLv3), sin cuenta, requiere Blender >=4.2,
  activamente mantenido (v2.0.16, 13 jun 2026, 1097 commits) —
  candidato viable para generar la malla base humanoide (confianza alta,
  3-0). Fuente: `github.com/makehumancommunity/mpfb2`.
- **Riggeo sin Mixamo**: dos rutas gratuitas confirmadas — (a)
  `Motion-capture-connector`, addon que retargetea BVH a rigs MB-Lab/
  Makehuman/Rigify parcial, pero es código de la era Blender 2.8 (su
  compatibilidad con Blender 4.x/Rigify moderno no está verificada); (b)
  el sistema nativo de constraints de Blender (Copy Rotation/Location +
  Bake Action) como alternativa 100% gratuita al addon de pago
  Auto-Rig Pro (confianza alta, 3-0 ambas).
- **Export**: glTF-Transform CLI ofrece Draco (`KHR_draco_mesh_compression`,
  solo geometría/vértices) vs Meshopt (`EXT_meshopt_compression`,
  geometría **y** datos de animación) — relevante porque este pipeline
  necesita clips de animación esquelética embebidos (confianza alta, 3-0).
- **Generadores IA text-to-3D locales** (TripoSR, InstantMesh, Wonder3D):
  sus números de rendimiento (velocidad, VRAM) tienen confianza alta
  (3-0 unánime), **pero** las claims de que corren "100% local sin
  cuenta" y que sus licencias permiten uso profesional/comercial
  libremente fueron **refutadas** (0-3, 0-3, 1-2) en la verificación
  adversarial — no se usan como ruta primaria en este plan (ver decisión
  3 del README).
- **Outline en Three.js**: el `OutlinePass` oficial (post-procesamiento
  vía `EffectComposer`) opera en screen-space sobre la silueta
  rasterizada final, por lo que funciona sobre cualquier malla
  (rígida o esquelética) sin depender de inflar normales sobre la
  geometría fuente — a diferencia del inverted-hull actual, que sí
  depende de eso y es frágil bajo deformación de skinning (confianza
  alta, 3-0 ambas claims).
- **Shading painterly de Puss in Boots**: dos técnicas documentadas por
  el VFX Supervisor de DreamWorks (Mark Edwards) en prensa especializada
  — (1) rim light como decisión estilística deliberada, desacoplada de
  la física real ("cheated" por legibilidad, confianza alta 3-0),
  portable a un `ShaderMaterial` custom; (2) "stamp maps" (nubes de
  puntos procedurales proyectadas con coherencia temporal para simular
  pinceladas, confianza media 2-1, sin paper técnico peer-reviewed —
  sirve de inspiración conceptual, no de receta exacta). Esto es
  insumo para la Etapa 2 (fuera de este plan).
- **Puentes Claude Code ↔ Blender**: existe `claude-blender` (MCP
  server open-source, MIT, 20+ tools incluyendo ejecutar bpy arbitrario),
  pero es de baja actividad y no verificado para producción (confianza
  media, 2-1) — se descarta como dependencia; la ruta recomendada es
  invocar `blender --background --python script.py` directo vía Bash.

### Lo que quedó sin responder (open questions del research)

1. Licencias reales de los pesos de TripoSR/InstantMesh/Wonder3D
   (motivo para excluirlos de este plan, no para resolver aquí).
2. Compatibilidad real de `Motion-capture-connector` con Blender 4.x +
   Rigify moderno (por eso este plan usa keyframing manual, no ese addon).
3. **Presupuesto real de draw calls/vértices/VRAM** de un humanoide
   rigged + `OutlinePass` en Three.js — ninguna claim verificada dio un
   número confiable. Se convierte en tarea de medición de este plan
   (AC-8).
4. Madurez de `claude-blender` — no se usa en este plan (decisión 10).

## 2. Solución propuesta

Construir el pipeline completo en una **app nueva** (`apps/journey-realistic`,
copia de `apps/journey`) para no arriesgar la app en producción, cubriendo
solo **Etapa 1**: un NPC humanoide con geometría/rig/animación
creíbles (sin textura pintada todavía), cargado en Three.js con la misma
interfaz pública que ya usa el resto del motor.

### Decisiones clave

Ver la lista completa (12 decisiones) en
[README.md](README.md#decisiones-no-reabribles). Resumen del flujo de
decisión: **MPFB2** (malla, sin cuenta) → **Rigify** (rig, sin cuenta) →
**keyframing manual** (animación, sin cuenta, sin depender de un addon
no verificado) → **glTF-Transform + Meshopt** (export) → **GLTFLoader +
SkinnedMesh + AnimationMixer** (runtime) → **OutlinePass** (contorno,
reemplaza inverted-hull solo para NPCs) → **medición real** (nuevo
presupuesto de draw calls, no uno inventado).

### Constraints considerados

- Sin cuenta/registro en ninguna herramienta (restricción dura del dueño).
- Sin depender de licencias no verificadas (por eso se descartan los
  generadores IA como ruta primaria).
- No romper `apps/journey` ni su regla de `<100 draw calls/sala`.
- La interfaz pública de `character.ts` (`CharacterHandle`/`NpcHandle`)
  se preserva para no tener que tocar `rooms/`, `dialog.ts`, `hud.ts`.

## 3. Criterios de Aceptación (AC)

- **AC-1**: Given el monorepo actual, When se crea `apps/journey-realistic`
  como copia de `apps/journey`, Then el nuevo paquete
  `@portfolio/journey-realistic` compila
  (`pnpm --filter @portfolio/journey-realistic run build`) sin tocar
  `apps/journey`.
- **AC-2**: Given Blender >=4.2 con el addon MPFB2 instalado localmente,
  When se corre el script headless de generación de malla, Then se
  produce un `.blend` con una malla humanoide base de topología limpia
  (manifold, sin n-gons rotos) sin abrir la GUI de Blender.
- **AC-3**: Given la malla base generada, When se aplica el rig Rigify
  (metarig humanoide + generate rig), Then el `.blend` resultante tiene
  un armature deformando la malla correctamente en una pose de prueba,
  sin artefactos de piel rota.
- **AC-4**: Given el rig generado, When se crean los clips de animación
  walk/idle/talk/sit por keyframing manual sobre el rig Rigify, Then cada
  clip queda exportable como una `AnimationClip` reconocible por
  `AnimationMixer` de Three.js (nombre de acción consistente).
- **AC-5**: Given el `.blend` final (malla + rig + animaciones), When se
  exporta con glTF-Transform CLI (compresión Meshopt), Then se genera un
  `.glb` cargable por `GLTFLoader` sin errores de parseo, con tamaño
  documentado.
- **AC-6**: Given el `.glb` exportado, When se carga en
  `apps/journey-realistic` reemplazando la implementación interna de
  `character.ts`, Then la interfaz pública actual (`setWalking`,
  `setPose`, `setHeadYaw`, `update`, `setVisible`, `dispose`) sigue
  funcionando sin cambios en los call-sites de `rooms/`, `dialog.ts` ni
  `hud.ts`.
- **AC-7**: Given un NPC humanoide `SkinnedMesh` animándose, When se
  aplica `OutlinePass` vía `EffectComposer`, Then el contorno se ve
  correcto durante la animación (sin los artefactos que sí aparecerían
  con inverted-hull sobre geometría deformada por skinning).
- **AC-8**: Given una escena de prueba con 1 NPC humanoide + `OutlinePass`,
  When se mide con `renderer.info.render.calls` en desktop y en un
  dispositivo/emulación móvil de gama media, Then el número real de draw
  calls/vértices queda documentado y se propone un presupuesto de sala
  nuevo para `apps/journey-realistic` (la regla `<100` de
  `journey-rooms.md` sigue aplicando solo a `apps/journey`).
- **AC-9**: Given el NPC final sin textura pintada (Etapa 1), When se
  compara visualmente con el NPC procedural actual, Then la silueta/
  anatomía se percibe más creíble (validación humana del dueño, no
  automatizable).
- **AC-10**: Given las herramientas usadas (MPFB2, Rigify, glTF-Transform,
  Blender), When se documentan sus licencias, Then queda registrado que
  ninguna requiere cuenta/registro y que los assets generados son
  reutilizables en un portfolio público (MPFB2: código GPLv3 + licencia
  de assets a verificar puntualmente; Rigify: parte de Blender, GPL;
  glTF-Transform: Apache-2.0/MIT).
- **AC-11**: Given el pipeline Blender, When se invoca headless, Then
  existe un comando devtools (`python devtools/run.py npc_pipeline
  <subcomando>`) que orquesta cada etapa (generate-mesh/rig/animate/
  export) sin requerir abrir Blender GUI.
- **AC-12**: Given el trabajo terminado localmente, When se completa la
  batería de verificación (sección 9 de este plan), Then NO se hace
  push/PR/deploy automático — queda local para que el dueño pruebe
  primero (`pnpm --filter @portfolio/journey-realistic run dev`).

## 4. Diagrama de Flujo (Antes y Despues)

### Antes (procedural, `apps/journey`)

```text
makeNpc(spec)
  --> primitivas (Box/Sphere/Cone) x N partes del cuerpo
  --> mergeGeometries() por material
  --> CanvasTexture (cara: ojos + parpadeo)
  --> toonMat() + outlineGroup() [inverted-hull, por-NPC, ~10-16 draw calls]
  --> Group (poses = transforms manuales por tipo: idle/walk/fight/...)
```

### Después (rigged, `apps/journey-realistic`, Etapa 1)

```text
[offline — Blender headless, una vez por template de NPC]
MPFB2 (malla base) --> Rigify (rig) --> keyframing manual
  (walk/idle/talk/sit) --> glTF-Transform export (Meshopt)
  --> npc-base.glb

[runtime — Three.js, por cada instancia de NPC]
GLTFLoader.load(npc-base.glb)
  --> SkinnedMesh + AnimationMixer (clips reusados, sin retargeting)
  --> EffectComposer + OutlinePass (contorno screen-space, 1 vez/escena)
  --> misma interfaz CharacterHandle/NpcHandle (setPose/setWalking/...)
```

## 5. Diagrama ER

N/A — no hay cambios en modelos de datos ni en content collections. Los
tipos TypeScript existentes (`RoomId`, `CharacterSpec`, `CharacterPose`)
se preservan; ver decisión 7 del README.
