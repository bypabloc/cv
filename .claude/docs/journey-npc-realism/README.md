# NPCs 3D humanoides realistas (painterly) — knowledge tree

> Research profundo (workflow `deep-research`, 2026-07-06: 112 agentes,
> 29 fuentes, 103 claims extraídas, 25 verificadas con voto adversarial
> 3-vías — 19 confirmadas, 6 refutadas) sobre cómo reemplazar los NPCs
> 100% procedurales de `apps/journey` (primitivas fusionadas + toon +
> inverted-hull, ver `src/engine/character.ts`) por humanoides `.glb`
> riggeados y creíbles, con un pipeline 100% local y sin cuenta
> (Blender headless + Three.js). Implementado en la app experimental
> `apps/journey-realistic` — ver el plan
> `docs/specs/journey-npc-realism/` (efímero, task-tracking) para el
> estado de ejecución; ESTE documento es la referencia técnica
> permanente del dominio.

## Cuando leer

| Documento | Cuando leer |
|-----------|-------------|
| [01-pipeline-blender-headless.md](01-pipeline-blender-headless.md) | Antes de generar/riggear/animar un humanoide con Blender headless (MPFB2 + Rigify + keyframing), o al diagnosticar un script `bpy` que falla |
| [02-export-y-threejs-integracion.md](02-export-y-threejs-integracion.md) | Antes de exportar a `.glb` (Draco vs Meshopt) o de cablear `GLTFLoader`/`SkinnedMesh`/`AnimationMixer`/`OutlinePass` en Three.js |
| [03-painterly-shading-y-generadores-ia.md](03-painterly-shading-y-generadores-ia.md) | Antes de trabajar la Etapa 2 (textura painterly estilo "Gato con Botas") o de evaluar un generador IA text-to-3D como TripoSR/InstantMesh/Wonder3D |
| [04-prompts-claude-code.md](04-prompts-claude-code.md) | Al pedirle a Claude Code que escriba/corra los scripts del pipeline — prompts de ejemplo + el patrón de iteración render→leer PNG→ajustar |

## Reglas críticas (resumen)

- **SIEMPRE** el pipeline es 100% local y sin cuenta/registro de ningún
  tipo (restricción dura del proyecto). Blender headless
  (`blender --background --python script.py`) es el eje.
- **SIEMPRE** malla base vía **MPFB2** (addon Blender, GPLv3, gratis,
  sin cuenta, requiere Blender >=4.2). **NUNCA** generadores IA
  text-to-3D (TripoSR/InstantMesh/Wonder3D) como ruta primaria — sus
  claims de "100% local sin cuenta" y licencia permisiva para uso
  profesional fueron **refutadas** en la verificación adversarial (ver
  [03-painterly-shading-y-generadores-ia.md](03-painterly-shading-y-generadores-ia.md)).
- **SIEMPRE** rig vía **Rigify** (incluido en Blender, gratis, sin
  cuenta). **NUNCA** Mixamo (requiere cuenta Adobe).
- **SIEMPRE** animación por keyframing manual sobre el rig Rigify
  (reutilizado en todas las instancias, sin retargeting per-personaje).
  El addon `Motion-capture-connector` (BVH retargeting) es OPCIONAL y su
  compatibilidad con Blender 4.x/Rigify moderno NO está verificada
  (código de la era Blender 2.8).
- **SIEMPRE** export con **glTF-Transform CLI + Meshopt** (comprime
  geometría Y animación) — Draco solo comprime geometría.
- **SIEMPRE** el contorno de NPCs humanoides `SkinnedMesh` usa
  **`OutlinePass`** (post-proceso screen-space vía `EffectComposer`).
  **NUNCA** el inverted-hull actual de `toon.ts` sobre `SkinnedMesh` —
  depende de inflar normales sobre la geometría FUENTE y es frágil bajo
  deformación de skinning.
- **NUNCA** asumir un presupuesto de draw calls/sala sin medir: no hay
  ningún número confiable en el research para un humanoide rigged +
  `OutlinePass` — se mide con `renderer.info.render.calls` en cada caso.
- **SIEMPRE** verificar la licencia real (archivo `LICENSE`, no el
  abstract/marketing del repo) de cualquier herramienta antes de
  adoptarla para uso en un portfolio público/profesional.

## Estado del research

25 claims verificadas con voto adversarial 3-vías (2/3 refutan mata la
claim): **19 confirmadas**, **6 refutadas**. Las 6 refutaciones caen
todas en el mismo eje — licencias/"sin cuenta" de los generadores IA
locales (ver
[03-painterly-shading-y-generadores-ia.md](03-painterly-shading-y-generadores-ia.md))
y una claim específica sobre el costo de Jump Flood Algorithm como
alternativa de outline (sin benchmarking directo, no usar ese número).

## Documentos relacionados

- Plan de implementación (efímero, task-tracking):
  `docs/specs/journey-npc-realism/`
- App experimental: `apps/journey-realistic/` (copia de `apps/journey`,
  no deployada)
- Canon de sala de `apps/journey` (NO se edita por este trabajo):
  [.claude/rules/journey-rooms.md](../../rules/journey-rooms.md)
- Skill invocable: [`/journey-npc-realism`](../../skills/journey-npc-realism/SKILL.md)
