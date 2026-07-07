# 6-7. Tests requeridos y archivos afectados

## 6. Tests requeridos

### 6.A. `devtools/npc_pipeline/` (Python, pytest — SÍ tiene tests)

A diferencia de los scripts `bpy` (que corren dentro de Blender y son
difíciles de testear con pytest convencional), la capa de orquestación
en `devtools/npc_pipeline/` es Python puro (parsing de flags, armado del
comando `subprocess`, parseo de exit codes) y **sigue el estándar de
`python.md`**: pytest, BDD-style en el docstring, asserts exactos,
coverage >= 80% per-file.

```text
WHEN se invoca `npc_pipeline generate-mesh --output=X`
THEN se arma el comando `blender --background --python generate_mesh.py -- --output=X`
```

```text
WHEN Blender no esta en PATH
THEN `npc_pipeline status` retorna exit code 1 con mensaje claro (no traceback)
```

Mockear: `subprocess.run` (no se invoca Blender real en unit tests).
NO mockear: el parsing de flags propio.

### 6.B. `apps/journey-realistic` (hereda la exención de `apps/journey`)

`apps/journey` está exenta de tests unit Vitest (PR #306,
`.claude/rules/astro-landing.md` + cross-ref en `journey-rooms.md`) por
ser Three.js vanilla manga-ink — la misma razón aplica a su copia. La
verificación de la app es:

- **Typecheck**: `astro check` + `tsc --noEmit`.
- **Lint**: `biome check`.
- **Build**: `pnpm --filter @portfolio/journey-realistic run build`.
- **Smoke visual headless** (Playwright, patrón existente
  `tmp/journey-smoke-perf.py` adaptado): cargar la escena de prueba con
  el NPC nuevo, esperar a que el render se estabilice, capturar
  `renderer.info.render.calls`/`triangles` y un screenshot.

### 6.C. Validación visual humana (no automatizable)

AC-9 (silueta más creíble que el NPC procedural actual) y la calidad de
las poses/animación requieren revisión del dueño del proyecto —
documentado explícitamente como paso manual, no un test automatizado.

### 6.D. E2E completo

No aplica un E2E de flujo de usuario nuevo (no hay una feature de UI
nueva, es un cambio de implementación interna del renderizado de NPCs).
El smoke de 6.B cubre la verificación de comportamiento observable.

## 7. Archivos afectados

### Crear

- `apps/journey-realistic/` (paquete completo, copia de `apps/journey`
  con las diferencias de la sección 04) — Verificar:
  `pnpm --filter @portfolio/journey-realistic run build`
- `apps/journey-realistic/src/engine/character.ts` (reescrito: carga
  `.glb` + `AnimationMixer`, misma interfaz pública) — Verificar: `astro
  check` + smoke visual (6.B)
- `apps/journey-realistic/src/engine/npc-outline.ts` (nuevo,
  `EffectComposer`/`OutlinePass` para NPCs) — Verificar: smoke visual,
  AC-7
- `apps/journey-realistic/public/models/npc-base.glb` (artefacto del
  pipeline, generado — no se edita a mano) — Verificar: `GLTFLoader`
  carga sin error (parte del smoke)
- `devtools/npc_pipeline/{__init__.py,main.py,flags.py,blender_runner.py,README.md}`
  — Verificar: `python devtools/run.py test_runner --module=devtools --type=unit`
- `devtools/npc_pipeline/scripts/{install_addons.py,generate_mesh.py,rig_mesh.py,export_glb.py}`
  (corren dentro de Blender) — Verificar: ejecución headless real
  (`blender --background --python <script> -- ...`) sin excepciones
- `devtools/tests/npc_pipeline/test_*.py` — Verificar: `pytest` verde,
  coverage >= 80%
- `docs/specs/journey-npc-realism/mpfb2-api-discovery.md` (spike,
  documentado antes de `generate_mesh.py`) — Verificar: contiene los
  operators reales usados por el script

### Modificar

- `.gitignore` — agregar `apps/journey-realistic/blender/assets/*.blend`
  y `tmp/npc-pipeline/` (artefactos intermedios pesados, no se
  commitean) — Verificar: `git status` no muestra esos paths tras correr
  el pipeline

### NO se modifica (explícito)

- `apps/journey/**` — ningún archivo de la app actual se toca.
- `.claude/rules/journey-rooms.md` — su regla `<100 draw calls/sala`
  sigue rigiendo solo `apps/journey`.
- `packages/content`, `packages/ui`, `packages/app-shared`, `packages/seo`
  — se consumen tal cual, sin cambios.
