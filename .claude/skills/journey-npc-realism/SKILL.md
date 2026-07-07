---
name: journey-npc-realism
description: >
  NPC 3D humanoid realism pipeline for the portfolio's journey app.
  Covers replacing the 100% procedural NPCs of apps/journey (merged
  primitives + canvas face + toon material + inverted-hull outline, no
  skeleton) with rigged .glb humanoids in the experimental app
  apps/journey-realistic, using a 100% local, no-signup pipeline:
  MPFB2 (free Blender addon, GPLv3) for the base mesh, Rigify (bundled
  in Blender) for the rig, manual keyframing for animation (no Mixamo),
  glTF-Transform CLI with Meshopt for export, and Three.js
  GLTFLoader + SkinnedMesh + AnimationMixer + OutlinePass for runtime
  loading (OutlinePass replaces the inverted-hull outline technique,
  which breaks on deforming SkinnedMesh). Also covers the painterly
  NPR shading research (Puss in Boots: The Last Wish style — rim light
  + "stamp maps") for a future Stage 2, and why local AI text-to-3D
  generators (TripoSR, InstantMesh, Wonder3D) are NOT used as the
  primary path (their "100% local, no account, permissive license"
  claims were explicitly refuted in adversarial verification). ALWAYS
  invoke this skill BEFORE answering ANY question about making 3D NPCs
  more realistic/credible, Blender headless bpy scripting for
  characters, MPFB2, Rigify without Mixamo, painterly/NPR shaders,
  OutlinePass vs inverted-hull on skinned meshes, or the
  apps/journey-realistic app. NEVER answer from training data alone —
  this portfolio has a consolidated 2026 research module (deep-research
  workflow, 112 agents, adversarial verification) with specific
  confirmed/refuted findings that override generic advice.
  Use when the user says "npc realista", "npc 3d humanoide", "personajes
  3d creibles", "npcs roboticos", "mejorar npcs journey", "blender
  headless", "bpy script", "mpfb2", "makehuman blender", "rigify",
  "riggear sin mixamo", "animar sin mixamo", "gltf transform",
  "draco vs meshopt", "outline pass three.js", "contorno skinned mesh",
  "inverted hull skinning", "painterly shader", "npr shading",
  "estilo gato con botas", "puss in boots style", "stamp maps",
  "triposr", "instantmesh", "wonder3d", "generador ia 3d local",
  "text-to-3d local sin cuenta", "journey-realistic", "journey realism",
  "claude-blender", "pipeline de personajes 3d", "malla humanoide
  blender", "skeletal animation three.js", "animationmixer three.js".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
argument-hint: "[mpfb2 | rigify | outline-pass | export | painterly | licencias]"
---

# NPCs 3D humanoides realistas (painterly) — journey-realistic

## Estado (2026-07-07)

Research profundo completado (workflow `deep-research`: 112 agentes, 6
ángulos, 29 fuentes, 103 claims extraídas, 25 verificadas — 19
confirmadas / 6 refutadas). Plan de implementación en
`docs/specs/journey-npc-realism/` (efímero). **Etapa 1 implementada y
verificada visualmente** (2026-07-07): pipeline Blender headless
completo (`devtools/npc_pipeline`: MPFB2 → Rigify → keyframing →
glTF-Transform) corriendo end-to-end, `.glb` real (idle+walk) cargando
y animando en `apps/journey-realistic` con `OutlinePass`, un NPC
reemplazado (`estudianteRonda` en la sala `aula`) confirmado en
navegador junto a los NPCs procedurales. Local-first: sin push/PR/deploy
hasta que el dueño lo pruebe (`pnpm --filter @portfolio/journey-realistic
run dev`). Hallazgos reales (no anticipados por el research) en
`docs/specs/journey-npc-realism/mpfb2-api-discovery.md` y en los docs
01-02 de `.claude/docs/journey-npc-realism/`.

## Decisiones que NO se reabren

1. App nueva (`apps/journey-realistic`), NO se toca `apps/journey`.
2. Solo Etapa 1 en el plan actual: geometría/rig/silueta + animación
   esquelética básica, sin textura pintada (Etapa 2 es un plan futuro).
3. Malla base: **MPFB2**, NO generadores IA text-to-3D (licencias
   refutadas, ver doc 03).
4. Rig: **Rigify** (incluido en Blender). Animación: keyframing manual,
   NO Mixamo (requiere cuenta).
5. Export: **glTF-Transform + Meshopt** (comprime geometría y
   animación; Draco solo geometría).
6. Contorno de NPCs: **`OutlinePass`** (screen-space) reemplaza el
   inverted-hull actual — solo para NPCs `SkinnedMesh`, los props
   estáticos de la sala no cambian.
7. Sin presupuesto de draw calls fijado a priori — se mide con
   `renderer.info.render.calls` (ver doc 02).
8. 100% herramientas locales sin cuenta: Blender headless vía Bash, sin
   `claude-blender` (MCP, descartado por baja madurez).

## Documentos relacionados

- Rule autoritativa de `apps/journey`:
  [.claude/rules/journey-rooms.md](../../rules/journey-rooms.md) (NO se
  edita por este trabajo — sigue rigiendo solo `apps/journey`)
- Docs detallados: [.claude/docs/journey-npc-realism/](../../docs/journey-npc-realism/)
  - [README.md](../../docs/journey-npc-realism/README.md) — índice +
    reglas críticas
  - [01-pipeline-blender-headless.md](../../docs/journey-npc-realism/01-pipeline-blender-headless.md)
    — MPFB2 + Rigify + animación
  - [02-export-y-threejs-integracion.md](../../docs/journey-npc-realism/02-export-y-threejs-integracion.md)
    — glTF-Transform + GLTFLoader/AnimationMixer/OutlinePass
  - [03-painterly-shading-y-generadores-ia.md](../../docs/journey-npc-realism/03-painterly-shading-y-generadores-ia.md)
    — técnica Puss in Boots + por qué NO usar TripoSR/InstantMesh/Wonder3D
  - [04-prompts-claude-code.md](../../docs/journey-npc-realism/04-prompts-claude-code.md)
    — prompts de ejemplo + patrón de iteración render→leer PNG→ajustar
- Plan de implementación (efímero):
  `docs/specs/journey-npc-realism/README.md`
- Devtools nuevo: `devtools/npc_pipeline/` (orquesta Blender headless)
