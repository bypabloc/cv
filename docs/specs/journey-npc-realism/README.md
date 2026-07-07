# Plan: NPCs humanoides creíbles (painterly) en una app nueva `journey-realistic`

> Los NPCs de `apps/journey` son 100% procedurales (primitivas fusionadas +
> cara en canvas + toon material + contorno inverted-hull, sin
> skeleton/rig — ver `src/engine/character.ts`) y el dueño del proyecto los
> describe como "robóticos y horribles". Este plan, basado en un research
> profundo (workflow `deep-research`, 2026-07-06: 112 agentes, 29 fuentes,
> 19 claims confirmadas / 6 refutadas), propone un pipeline 100% local y
> sin cuenta (Blender headless + Three.js) para reemplazarlos por
> humanoides `.glb` riggeados, en una app **nueva** (`apps/journey-realistic`,
> copia de `apps/journey`) que no toca la app actual en producción.
>
> Alcance de ESTE plan: **Etapa 1 únicamente** — geometría/rig/silueta
> anatómica creíble + animación esquelética básica, SIN la textura
> painterly pintada (Etapa 2, plan futuro separado).

## Cuando leer cada archivo

| Archivo | Cuando leer |
|---------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Contexto completo, hallazgos clave del research, decisiones no-reabribles y los 12 criterios de aceptación (AC-1 a AC-12) |
| [02-blender-pipeline-etapa1.md](02-blender-pipeline-etapa1.md) | Workflow Blender headless (bpy): MPFB2 (malla) → Rigify (rig) → keyframing (animación) → glTF-Transform (export), con scripts y los prompts de Claude Code para ejecutarlo |
| [03-threejs-integracion.md](03-threejs-integracion.md) | Carga del `.glb` (GLTFLoader + SkinnedMesh + AnimationMixer), reemplazo del inverted-hull por `OutlinePass`, y el plan de medición para el presupuesto de draw calls nuevo |
| [04-nueva-app-scaffold.md](04-nueva-app-scaffold.md) | Cómo se crea `apps/journey-realistic` como copia de `apps/journey`, qué se comparte vs qué se bifurca, y el comando devtools `npc_pipeline` nuevo |
| [05-tests-y-archivos.md](05-tests-y-archivos.md) | Qué se verifica de cada pieza (la app hereda la exención de tests unit de `apps/journey`) + listado completo de archivos afectados |
| [06-descomposicion-tareas.md](06-descomposicion-tareas.md) | Tareas atómicas, sus AC referenciados y qué se puede paralelizar |
| [07-commits.md](07-commits.md) | Commits incrementales planeados |
| [08-paralelizacion-worktrees.md](08-paralelizacion-worktrees.md) | Por qué el pipeline es mayormente secuencial y los 2 puntos donde SÍ vale un worktree |
| [09-verificacion-e2e.md](09-verificacion-e2e.md) | Batería de verificación final + Definition of Done |

## Estado

| Fase | Estado |
|------|--------|
| Research profundo (`deep-research` workflow) | Hecho (2026-07-06) |
| Spec/plan creado | Hecho (este documento) |
| Implementación (T1-T12) | Hecho (2026-07-07): pipeline Blender headless completo, `.glb` real cargando y animando en `apps/journey-realistic`, verificado visualmente en navegador (ver `09-verificacion-e2e.md`) |
| T13 (validación visual del dueño + go/no-go Etapa 2) | Pendiente — local-first, sin push/PR/deploy hasta que el dueño confirme (`pnpm --filter @portfolio/journey-realistic run dev`) |

## Decisiones no reabribles

1. **App nueva, no se toca `apps/journey`**: `apps/journey-realistic` es una
   copia; `apps/journey` sigue deployado tal cual está. Los packages
   compartidos (`@portfolio/content`, `@portfolio/ui`, `@portfolio/app-shared`,
   `@portfolio/seo`) se siguen consumiendo via `workspace:*`; solo el motor 3D
   (`engine/`, `character.ts`, `toon.ts`, `rooms/`) se bifurca. Detalle:
   [04-nueva-app-scaffold.md](04-nueva-app-scaffold.md).
2. **Este plan cubre SOLO Etapa 1** (geometría/rig/silueta + animación
   esquelética básica, material toon/flat simple). La Etapa 2 (textura
   painterly estilo "Gato con Botas: El Último Deseo") es un plan futuro
   separado que arranca cuando el dueño valide visualmente Etapa 1.
3. **Malla base humanoide vía MPFB2** (addon Blender GPLv3, gratis, sin
   cuenta, requiere Blender >=4.2, activamente mantenido — verificado
   3-0 en el research). **NO** se usan generadores IA text-to-3D
   (TripoSR/InstantMesh/Wonder3D): sus claims de "100% local sin cuenta"
   y de licencia permisiva para uso profesional/comercial fueron
   **explícitamente refutadas** en la verificación adversarial del
   research (votos 0-3, 0-3, 1-2). Quedan como exploración futura
   opcional solo si alguien re-lee a mano el `LICENSE` real de cada repo.
4. **Rig vía Rigify** (incluido en Blender, gratis, sin cuenta) sobre la
   malla MPFB2.
5. **Animación por keyframing manual** sobre el rig Rigify (no
   `Motion-capture-connector`: su compatibilidad con Blender 4.x/Rigify
   moderno no está verificada, es código de la era Blender 2.8). Como
   todos los NPCs comparten UN rig base, los clips se crean UNA vez y se
   reutilizan en todas las instancias — sin retargeting por-personaje.
6. **Export con glTF-Transform CLI + Meshopt** (no Draco): Meshopt
   comprime geometría Y datos de animación; Draco solo geometría.
7. **La interfaz pública `NpcHandle` de `character.ts` NO cambia**
   (`group`, `update`, `collider`, `talk`, `endTalk`, `jump`, `dispose`).
   Implementación real (ajustada durante T9, ver nota en
   `09-verificacion-e2e.md`): en vez de reescribir `makeCharacter`/
   `makeNpc` por completo (que degradaría a idle/walk todo NPC con pose
   fija, ya que Etapa 1 solo generó esos 2 clips), se agregó el adaptador
   `spawnRealisticNpc(opts): NpcHandle` en `npc-gltf-loader.ts` —
   mismo contrato, respaldado por el `.glb` real — usado para reemplazar
   UN NPC (`estudianteRonda` en `aula.ts`, el único sin pose fija) sin
   tocar `dialog.ts` ni `hud.ts`. Un swap total queda para cuando existan
   los 5 clips restantes (`fight`/`sit`/`kneel`/`wave`/`talk`).
8. **El contorno de los NPCs humanoides pasa a `OutlinePass`**
   (post-procesamiento screen-space vía `EffectComposer`), porque
   funciona sobre `SkinnedMesh` deformándose; el inverted-hull actual
   depende de inflar normales sobre la geometría fuente y es frágil bajo
   skinning (confirmado 3-0 en el research, y confirmado de nuevo
   renderizando: contorno correcto durante el walk cycle, AC-7). Los
   props/paredes estáticos de la sala **no se tocan** — siguen con
   `mergedBoxes`/`outlinedMergedBoxes`. Hallazgo no anticipado: la
   composición final de `OutlinePass` usa `AdditiveBlending` — un color
   oscuro (el `#141018` ink de `toon.ts`) es invisible ahí; el contorno
   real usa un glow claro (`#f5f2ea`), no una réplica exacta del ink
   manga (detalle en `mpfb2-api-discovery.md`).
9. **Sin presupuesto de draw calls fijado a priori**: se mide
   empíricamente durante la ejecución (AC-8) y se documenta como el
   presupuesto propio de `apps/journey-realistic`. La regla `<100/sala`
   de `journey-rooms.md` sigue aplicando SOLO a `apps/journey` — no se
   edita esa rule en este plan.
10. **100% herramientas locales sin cuenta**: Blender headless
    (`blender --background --python script.py`) invocado por Claude Code
    vía su tool Bash. Se descarta `claude-blender` (bridge MCP) como
    dependencia: es un proyecto comunitario de baja actividad, no
    verificado para producción (research, confianza "medium").
11. **local-first**: implementación, commits y verificación quedan
    LOCALES. Sin push/PR/deploy automático — se avisa al dueño el comando
    de dev para que pruebe primero en el navegador, igual que el resto de
    planes de `journey` en curso (memoria `journey-local-first-workflow`).
12. **Sin deploy en este plan**: `apps/journey-realistic` no se conecta a
    Cloudflare Pages, no gana subdominio ni entra al matrix de CI/CD. Es
    un banco de pruebas local. Productivizarla (deploy, dominio) es una
    decisión futura, fuera de este plan.

## Referencias

- Research completo: workflow `deep-research`, run `wf_dc567e0e-042`
  (journal en `subagents/workflows/wf_dc567e0e-042/journal.jsonl`).
- [.claude/rules/journey-rooms.md](../../../.claude/rules/journey-rooms.md)
  — canon de sala vigente de `apps/journey` (NO se edita en este plan).
- [.claude/rules/plan-format.md](../../../.claude/rules/plan-format.md)
  — formato de este documento.
- [.claude/rules/devtools.md](../../../.claude/rules/devtools.md) —
  convención de scripts nuevos en `devtools/` (usada por `npc_pipeline`).
