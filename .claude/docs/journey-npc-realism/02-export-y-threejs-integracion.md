# Export a `.glb` + integración en Three.js

> [Indice](README.md) | Anterior: [pipeline Blender](01-pipeline-blender-headless.md) | Siguiente: [painterly + generadores IA](03-painterly-shading-y-generadores-ia.md)
>
> Verificado corriendo el pipeline real end-to-end (2026-07-07): `.glb`
> cargando, animando (idle/walk) y contorneado con `OutlinePass` en
> `apps/journey-realistic`, confirmado en navegador. Detalle completo:
> `docs/specs/journey-npc-realism/mpfb2-api-discovery.md` +
> `09-verificacion-e2e.md` (números reales de AC-8).

## Export: dos pasos (nativo + compresión)

```bash
# 1. Export crudo con el exportador nativo de Blender (glTF2, incluido)
blender --background --python devtools/npc_pipeline/scripts/export_glb.py \
  -- --input=apps/journey-realistic/blender/assets/npc-rigged.blend \
     --output=tmp/npc-pipeline/npc-base.raw.glb

# 2. Comprimir con glTF-Transform CLI
npx --yes @gltf-transform/cli meshopt \
  tmp/npc-pipeline/npc-base.raw.glb \
  apps/journey-realistic/public/models/npc-base.glb
```

```python
# export_glb.py — operator nativo de Blender
bpy.ops.export_scene.gltf(
    filepath=output_path,
    export_format='GLB',
    export_animations=True,
    export_skins=True,
    export_apply=True,
)
```

### Draco vs Meshopt (glTF-Transform CLI)

| Compresión | Comprime | Cuándo usarla |
|-----------|----------|----------------|
| `draco` (`KHR_draco_mesh_compression`) | Solo geometría/vértices | Mallas estáticas sin animación |
| `meshopt` (`EXT_meshopt_compression`) | Geometría **y** datos de animación (bufferViews genéricos) | **Este pipeline** — los `.glb` llevan clips esqueléticos embebidos |

Confirmado vía la documentación oficial de `gltf-transform.dev/cli`
(confianza alta, 3-0 en la verificación adversarial).

## Carga en Three.js: `GLTFLoader` requiere el decoder de Meshopt

El `.glb` final está comprimido con Meshopt (paso anterior). Cargarlo
con `GLTFLoader` sin registrar el decoder lanza
`"setMeshoptDecoder must be called before loading compressed files"` —
confirmado en el primer intento de carga real:

```typescript
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js'

const loader = new GLTFLoader()
loader.setMeshoptDecoder(MeshoptDecoder)   // OBLIGATORIO antes de loadAsync
```

## Carga en Three.js: adaptador `NpcHandle`, no un swap total de `character.ts`

Etapa 1 solo generó 2 clips (`idle`/`walk`) — las poses `fight`/`sit`/
`kneel`/`wave`/`talk` no existen todavía como `AnimationClip`.
Reescribir `makeCharacter`/`makeNpc` por completo degradaría a
idle/walk cualquier NPC con pose fija en las 10 salas de
`apps/journey-realistic` (regresión visual amplia). La implementación
real usa un **adaptador nuevo** con el MISMO contrato `NpcHandle`
(`group`/`update`/`collider`/`talk`/`endTalk`/`jump`/`dispose`),
reservado para NPCs de patrulla sin pose fija:

```typescript
import {
  AnimationMixer, Group, type Object3D,
} from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js'
import { clone as cloneSkeleton } from 'three/examples/jsm/utils/SkeletonUtils.js'

const loader = new GLTFLoader()
loader.setMeshoptDecoder(MeshoptDecoder)

let cachedBase: Promise<{ scene: Object3D; animations: AnimationClip[] }> | null = null
function loadCachedBase(url: string) {
  cachedBase ??= loader.loadAsync(url).then((gltf) => ({
    scene: gltf.scene, animations: gltf.animations,
  }))
  return cachedBase
}

export function spawnRealisticNpc(opts: NpcOpts): NpcHandle {
  const group = new Group()  // sincrono: se puebla cuando resuelve el fetch
  loadCachedBase('/models/npc-base.glb').then((base) => {
    // cloneSkeleton() (export `clone` de SkeletonUtils.js) es OBLIGATORIO
    // para clonar un SkinnedMesh — Object3D.clone() nativo NO preserva el
    // binding skeleton<->mesh.
    const object = cloneSkeleton(base.scene)
    const mixer = new AnimationMixer(object)
    group.add(object)
    // clip.name matchea CharacterPose exacto ('idle'/'walk') — ver
    // 01-pipeline-blender-headless.md (el track de export se nombra
    // igual a la accion, sin sufijo).
  })
  return { group, update, collider, talk, endTalk, jump, dispose }
}
```

Un swap total de `character.ts` queda para cuando existan los 5 clips
restantes. Detalle de la decisión: `docs/specs/journey-npc-realism/
09-verificacion-e2e.md` ("Nota sobre el alcance real de AC-6").

Cada instancia clonada comparte geometría/materiales (barato en
memoria) pero tiene su propio esqueleto + `AnimationMixer` (necesario
para animar independientemente).

## Contorno: `OutlinePass` reemplaza el inverted-hull para NPCs

El inverted-hull actual (`outlineGroup` en `toon.ts`) infla normales de
la geometría FUENTE y dibuja una segunda pasada con front-face
culling — funciona sobre geometría estática fusionada, pero es frágil
sobre `SkinnedMesh` deformándose (confirmado 3-0: depende de la
preparación de la malla fuente, no del resultado final renderizado).

`OutlinePass` (`three/examples/jsm/postprocessing/OutlinePass.js`,
oficial) opera en **screen-space**: renderiza la silueta de los objetos
seleccionados a un render target de máscara + detección de bordes —
funciona sobre cualquier malla ya deformada en el frame actual, sin
preparación especial de la geometría fuente (confirmado 3-0).

```typescript
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { OutlinePass } from 'three/examples/jsm/postprocessing/OutlinePass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'

const composer = new EffectComposer(renderer)
composer.addPass(new RenderPass(scene, camera))

const outlinePass = new OutlinePass(new Vector2(width, height), scene, camera)
outlinePass.edgeStrength = 2.5
outlinePass.edgeThickness = 1
// OutlinePass compone el contorno con AdditiveBlending (ver hallazgo
// abajo) — un color oscuro tipo ink es invisible ahi. Blanco calido es
// lo mas cercano al manga-ink que esta tecnica puede dar.
outlinePass.visibleEdgeColor.set('#f5f2ea')
composer.addPass(outlinePass)
composer.addPass(new OutputPass())

outlinePass.selectedObjects = activeNpcMeshes // actualizar al entrar/salir NPCs
```

### Hallazgo: `OutlinePass` compone con `AdditiveBlending` — sin ink oscuro

Confirmado leyendo el código fuente instalado
(`three/examples/jsm/postprocessing/OutlinePass.js`, r0.170): el paso
final de composición (`getOverlayMaterial()`) usa
`blending: AdditiveBlending`. Un color casi negro (`#141018`, el ink
manga del resto de la sala) es **invisible** ahí sin importar
`edgeStrength` — confirmado renderizando: `edgeStrength=10` + `#141018`
no mostraba NADA; con un color claro (`#f5f2ea`) el contorno aparece
correctamente durante la animación, sin artefactos de skinning (AC-7).
**Conclusión**: `OutlinePass` sirve para un contorno tipo "glow" de
selección (su caso de uso clásico en editores), NO para replicar el ink
oscuro manga exacto de `toon.ts` — un contorno oscuro real requeriría
un shader de silueta propio (fuera de Etapa 1).

### Costo — números REALES medidos (no estimados)

Medido con 1 NPC humanoide (26 756 vértices / 14 517 triángulos) +
`OutlinePass` activo, en la sala `aula` de `apps/journey-realistic`
(smoke Playwright, `renderer.info` con `autoReset=false` + reset manual
por frame — necesario porque el composer dispara varios
`renderer.render()` internos por frame y el reset automático solo
dejaría contado el ÚLTIMO pase):

| Métrica | Desktop (1280x800) | Móvil emulado (390x844 DPR2) |
| --- | --- | --- |
| `renderer.info.render.calls` | 184 | 158 |
| `renderer.info.render.triangles` | 96 492 | 41 280 |
| Tamaño `.glb` final (Meshopt) | 1.4 MB | — |

Presupuesto propuesto para `apps/journey-realistic`: **<250 draw
calls/sala con hasta 2 NPCs realistas simultáneos** (detalle y
metodología completa en `docs/specs/journey-npc-realism/
09-verificacion-e2e.md`). Esto reemplaza la estimación teórica previa
("no hay número medido confiable") — ahora hay uno real.

- Props/paredes estáticos de la sala NO se tocan — siguen con
  `mergedBoxes`/`outlinedMergedBoxes`. Confirmado que ambas técnicas de
  contorno (inverted-hull en props + `OutlinePass` en NPCs GLTF)
  coexisten sin conflicto en la misma escena.

## Anti-patrones

| Anti-patrón | Por qué | Corrección |
|-------------|---------|------------|
| `Object3D.clone()` en un `SkinnedMesh` | No preserva el binding skeleton↔mesh | `clone` de `SkeletonUtils.js` (`cloneSkeleton`) |
| Reusar el inverted-hull sobre un NPC `SkinnedMesh` | Depende de geometría fuente estática, rompe bajo deformación | `OutlinePass` (screen-space) |
| Draco para un `.glb` con animación | Solo comprime geometría, no los clips | Meshopt (`EXT_meshopt_compression`) |
| Cargar un `.glb` Meshopt sin `setMeshoptDecoder` | `GLTFLoader` lanza `setMeshoptDecoder must be called before...` | Registrar `MeshoptDecoder` en el loader antes de `loadAsync` |
| Contorno oscuro (`#141018`) en `OutlinePass` | Composición `AdditiveBlending` — invisible sin importar `edgeStrength` | Color claro tipo glow (`#f5f2ea`); ink oscuro real necesitaría shader propio |
| Reescribir `character.ts` completo con solo 2 clips (`idle`/`walk`) | Degrada a idle/walk todo NPC con pose fija en las 10 salas | Adaptador `spawnRealisticNpc(): NpcHandle` para UN NPC sin pose fija |
| Leer `renderer.info` con post-proceso y `autoReset` default (true) | Cada `render()` interno del composer resetea el contador — solo queda el último pase | `renderer.info.autoReset = false` + `renderer.info.reset()` manual una vez por frame |
| Fijar un presupuesto de draw calls "a ojo" | El research no encontró ningún número confiable | Medir con `renderer.info.render.calls` en el caso real (ya hecho, ver tabla arriba) |
