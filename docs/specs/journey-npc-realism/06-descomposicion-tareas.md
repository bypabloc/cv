# 8. Descomposición para paralelización

13 tareas atómicas. El pipeline Blender (T4-T8) es mayormente
**secuencial por naturaleza** (cada etapa consume el `.blend` de la
anterior) — el detalle de qué SÍ se puede correr en paralelo está en
[08-paralelizacion-worktrees.md](08-paralelizacion-worktrees.md).

- **T1 — Scaffold `apps/journey-realistic`**
  - Archivos: `apps/journey-realistic/**` (copia de `apps/journey`), `.gitignore`
  - AC: AC-1
  - Depende de: ninguna
  - Paralelizable con: T2, T3
  - Verify: `pnpm --filter @portfolio/journey-realistic run build`
  - Done: build verde, puerto de dev distinto al de `apps/journey` (4327)

- **T2 — Scaffold `devtools/npc_pipeline` (orquestación, sin scripts bpy todavía)**
  - Archivos: `devtools/npc_pipeline/{__init__.py,main.py,flags.py,blender_runner.py,README.md}`, `devtools/tests/npc_pipeline/**`
  - AC: AC-11
  - Depende de: ninguna
  - Paralelizable con: T1, T3
  - Verify: `python devtools/run.py test_runner --module=devtools --type=unit`
  - Done: `npc_pipeline status` detecta correctamente si Blender está o no en `PATH`

- **T3 — Setup manual: Blender local + addon MPFB2**
  - Archivos: ninguno (acción del dev, no código)
  - AC: precondición de AC-2
  - Depende de: ninguna
  - Paralelizable con: T1, T2
  - Verify: `blender --version` >= 4.2
  - Done: zip de MPFB2 descargado y ubicado en `devtools/npc_pipeline/vendor/`

- **T4 — Spike: descubrir el API real de MPFB2**
  - Archivos: `docs/specs/journey-npc-realism/mpfb2-api-discovery.md`, `devtools/npc_pipeline/scripts/install_addons.py`
  - AC: precondición de AC-2
  - Depende de: T2, T3
  - Paralelizable con: ninguna (bloquea T5 en adelante)
  - Verify: el doc lista operators reales confirmados corriendo en la consola de Blender
  - Done: `install_addons.py` corre headless sin excepciones

- **T5 — Generar malla base (`generate_mesh.py`) + preview**
  - Archivos: `devtools/npc_pipeline/scripts/generate_mesh.py`, `apps/journey-realistic/blender/assets/npc-base.blend`
  - AC: AC-2
  - Depende de: T4
  - Paralelizable con: ninguna
  - Verify: preview PNG revisado (Claude vía Read tool o el dueño)
  - Done: silueta anatómica aprobada antes de seguir

- **T6 — Riggear con Rigify (`rig_mesh.py`) + validar deformación**
  - Archivos: `devtools/npc_pipeline/scripts/rig_mesh.py`, `.../npc-rigged.blend`
  - AC: AC-3
  - Depende de: T5
  - Paralelizable con: ninguna
  - Verify: preview de pose de prueba (brazo levantado) sin artefactos de piel
  - Done: aprobado

- **T7 — Animar (keyframing manual: idle/walk/talk/sit)**
  - Archivos: `.../npc-rigged.blend` (clips agregados)
  - AC: AC-4
  - Depende de: T6
  - Paralelizable con: ninguna
  - Verify: 4 `Action` nombradas presentes, playback correcto en Blender
  - Done: aprobado visualmente

- **T8 — Exportar a `.glb` (`export_glb.py` + glTF-Transform Meshopt)**
  - Archivos: `devtools/npc_pipeline/scripts/export_glb.py`, `apps/journey-realistic/public/models/npc-base.glb`
  - AC: AC-5
  - Depende de: T7
  - Paralelizable con: ninguna
  - Verify: tamaño de archivo documentado; test de carga con `GLTFLoader` sin error
  - Done: aprobado

- **T9 — Reescribir `character.ts` (carga `.glb`, misma interfaz pública)**
  - Archivos: `apps/journey-realistic/src/engine/character.ts`
  - AC: AC-6
  - Depende de: T8, T1
  - Paralelizable con: ninguna
  - Verify: `astro check` + smoke visual con animación corriendo
  - Done: `rooms/`, `dialog.ts`, `hud.ts` siguen funcionando sin cambios

- **T10 — `OutlinePass` para NPCs (`npc-outline.ts`)**
  - Archivos: `apps/journey-realistic/src/engine/npc-outline.ts`
  - AC: AC-7
  - Depende de: T9
  - Paralelizable con: ninguna
  - Verify: smoke visual, contorno correcto durante la animación
  - Done: aprobado

- **T11 — Medir performance (draw calls/triángulos/memoria, desktop+móvil)**
  - Archivos: `docs/specs/journey-npc-realism/09-verificacion-e2e.md` (sección de medición)
  - AC: AC-8
  - Depende de: T10
  - Paralelizable con: T12
  - Verify: los 4 números documentados (draw calls, triángulos, memoria, frame time)
  - Done: presupuesto de sala propuesto para `apps/journey-realistic`

- **T12 — Documentar licencias (MPFB2, Rigify, glTF-Transform)**
  - Archivos: `docs/specs/journey-npc-realism/README.md` (o archivo dedicado de licencias)
  - AC: AC-10
  - Depende de: T4 (una vez se sabe qué versión de addon se instaló)
  - Paralelizable con: T5-T11 (independiente, no toca los mismos archivos)
  - Verify: licencias documentadas con fuente (archivo LICENSE real, no marketing)
  - Done: aprobado

- **T13 — Validación visual final del dueño (AC-9) + decisión go/no-go Etapa 2**
  - Archivos: ninguno (decisión)
  - AC: AC-9, AC-12
  - Depende de: T11, T12
  - Paralelizable con: ninguna (cierra el plan)
  - Verify: N/A — validación subjetiva
  - Done: el dueño confirma que la silueta es más creíble, o pide ajustes puntuales antes de considerar Etapa 2
