# Integración en Three.js: GLTFLoader, AnimationMixer, OutlinePass, presupuesto

## Carga del `.glb` (reemplazo interno de `character.ts`)

El builder actual (`makeNpc`/el constructor del jugador en
`character.ts`) construye la geometría en código. En
`apps/journey-realistic` la implementación interna cambia a cargar el
`.glb` generado por el pipeline Blender, pero **la interfaz pública se
mantiene igual** (decisión 7 del README) para no tener que tocar
`rooms/`, `dialog.ts` ni `hud.ts`:

```typescript
import { AnimationMixer, type AnimationAction } from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { clone as cloneSkeleton } from 'three/examples/jsm/utils/SkeletonUtils.js'

const loader = new GLTFLoader()
// Cachear el GLTF parseado una sola vez (todas las instancias de NPC
// comparten el mismo asset — solo SkinnedMesh.clone() + su propio
// AnimationMixer por instancia).
const gltf = await loader.loadAsync('/models/npc-base.glb')

function spawnNpc(spec: CharacterSpec): NpcHandle {
  // cloneSkeleton() (export `clone` de SkeletonUtils.js) es necesario
  // porque Object3D.clone() nativo NO clona bones/skinning correctamente.
  const instance = cloneSkeleton(gltf.scene)
  const mixer = new AnimationMixer(instance)
  const actions = new Map<CharacterPose, AnimationAction>(
    gltf.animations.map((clip) => [clip.name as CharacterPose, mixer.clipAction(clip, instance)]),
  )
  // setPose/setWalking/update/dispose implementan la MISMA interfaz
  // que hoy expone character.ts, pero mueven al mixer en vez de
  // transformar partes del cuerpo a mano.
}
```

Nota: clonar un `SkinnedMesh` requiere el export `clone` de
`three/examples/jsm/utils/SkeletonUtils.js` (importado aqui como
`cloneSkeleton`; el modulo NO exporta un namespace `SkeletonUtils`), NO
`Object3D.clone()` nativo — el clone nativo no preserva el binding
skeleton↔mesh correctamente. Cada instancia clonada comparte la
geometría/textura
(barata en memoria) pero tiene su propio esqueleto y `AnimationMixer`
(necesario para que cada NPC anime independientemente).

## Reemplazo del contorno: `OutlinePass` en vez de inverted-hull

El inverted-hull actual (`outlineGroup` en `toon.ts`) infla las normales
de la geometría FUENTE y dibuja una segunda pasada con front-face
culling — funciona bien sobre geometría estática fusionada, pero es
frágil sobre `SkinnedMesh` deformándose (confirmado 3-0 en el research:
depende de la preparación de la malla fuente, no del resultado final
renderizado).

`OutlinePass` (oficial, `three/examples/jsm/postprocessing/OutlinePass.js`)
opera distinto: renderiza la silueta de los objetos seleccionados a un
render target de máscara y aplica detección de bordes + blur sobre esa
máscara — un mecanismo de **screen-space**, por lo que funciona sobre
cualquier malla ya deformada por el skinning del frame actual, sin
necesitar preparación especial de la geometría fuente.

```typescript
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { OutlinePass } from 'three/examples/jsm/postprocessing/OutlinePass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'

const composer = new EffectComposer(renderer)
composer.addPass(new RenderPass(scene, camera))

const outlinePass = new OutlinePass(new Vector2(width, height), scene, camera)
outlinePass.edgeStrength = 3
outlinePass.edgeThickness = 1
outlinePass.visibleEdgeColor.set('#141018') // tinta, consistente con el resto de journey
composer.addPass(outlinePass)
composer.addPass(new OutputPass())

// Cada frame (o al entrar/salir un NPC de la sala): actualizar la
// lista de objetos con contorno.
outlinePass.selectedObjects = activeNpcMeshes
```

### Costo arquitectónico (cualitativo — los números reales van en AC-8)

- El inverted-hull actual cuesta ~2 draw calls por NPC (geometría normal
  + geometría inflada), escalando linealmente con la cantidad de NPCs.
- `OutlinePass` agrega: (a) 1 render de máscara de los objetos
  seleccionados (costo ~similar a 1 draw call extra por NPC visible,
  no 2x), más (b) un número **fijo** de pasadas fullscreen (detección de
  bordes + 2 blur separables + composite) que **no escala** con la
  cantidad de NPCs — es un costo por-escena, no por-NPC.
- Esto sugiere que `OutlinePass` podría ser más barato que el
  inverted-hull actual a partir de cierta cantidad de NPCs por sala,
  pero esto es una hipótesis de arquitectura, **no un número medido** —
  el research no encontró ninguna claim verificable con cifras reales
  para este caso específico (ver open question 3 del research). Se mide
  en AC-8, no se asume aquí.
- Props/paredes estáticos de la sala NO se tocan (siguen con
  `mergedBoxes`/`outlinedMergedBoxes`, decisión 8 del README) — solo los
  NPCs humanoides pasan a `OutlinePass`. Esto implica que la escena
  tendrá temporalmente DOS técnicas de contorno coexistiendo (inverted-hull
  para props estáticos + OutlinePass para NPCs); validar visualmente que
  el grosor/color de línea se percibe consistente entre ambas (riesgo
  de inconsistencia visual a anotar en AC-9).

## Medición del presupuesto (AC-8)

No se fija un número a priori. Plan de medición:

1. Escena de prueba aislada en `apps/journey-realistic` con 1 NPC
   humanoide + `OutlinePass` + la iluminación estándar de una sala del
   canon (`journey-rooms.md`).
2. Leer `renderer.info.render.calls`, `renderer.info.render.triangles` y
   `renderer.info.memory.geometries/textures` tras el primer frame
   estable (patrón similar al smoke existente
   `tmp/journey-smoke-perf.py`, adaptado a esta app).
3. Repetir con 2, 4 y 6 NPCs simultáneos en la misma sala para ver cómo
   escala (lineal vs con meseta por el costo fijo de `OutlinePass`).
4. Repetir en un perfil de GPU móvil de gama media (emulación
   Playwright con throttling, o dispositivo real si está disponible).
5. Documentar los 4 números (draw calls, triángulos, memoria, tiempo de
   frame) en [09-verificacion-e2e.md](09-verificacion-e2e.md) y proponer
   un presupuesto de sala para `apps/journey-realistic` (reemplaza el
   `<100` heredado, que sigue rigiendo solo `apps/journey`).

## Fuera de scope de este plan (anotado para el futuro)

- **Instancing de `SkinnedMesh`**: Three.js no tiene soporte maduro y
  simple para instanciar mallas esqueléticas (cada instancia necesita su
  propia matriz de huesos). Si la medición del paso anterior muestra que
  el costo por-NPC sigue siendo alto, evaluar `BatchedMesh` (Three.js
  0.170+) o un esquema de vertex-texture-skinning compartido en un plan
  futuro — no se prescribe aquí por falta de evidencia.
- **LOD (level of detail)**: reducir el poly-count del NPC a distancia
  no se investigó en este research; queda como palanca futura si el
  presupuesto medido no alcanza.
