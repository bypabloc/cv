# 11-12. Verificación E2E iterativa + Definition of Done

## Parte A — Refactor de tests

N/A parcial: es una app nueva (no hay tests viejos de `apps/journey-realistic`
que referencien código eliminado, porque el código no existía antes de
este plan). Sí aplica un barrido para confirmar que `apps/journey` (la
app original) permanece intacta:

```bash
git diff --stat -- apps/journey/   # debe estar vacío
rg -l "journey-realistic" apps/journey/ 2>/dev/null   # debe estar vacío
```

## Parte B — Batería de comandos reales

Bucle "no parar hasta que funcione": ejecutar → si falla, diagnosticar →
corregir → re-ejecutar la suite completa → repetir. Coverage no aplica
(la app hereda la exención de tests unit; `devtools/npc_pipeline` sí
tiene su propio gate de coverage >= 80%).

```bash
# 1. devtools/npc_pipeline (Python)
python devtools/run.py test_runner --module=devtools --type=unit
python devtools/run.py test_runner --module=devtools --type=coverage

# 2. apps/journey-realistic (lint + typecheck + build)
pnpm --filter @portfolio/journey-realistic exec biome check .
pnpm --filter @portfolio/journey-realistic exec astro check
pnpm --filter @portfolio/journey-realistic exec tsc --noEmit
pnpm --filter @portfolio/journey-realistic run build

# 3. Pipeline Blender real (headless, sin GUI)
python devtools/run.py npc_pipeline status
python devtools/run.py npc_pipeline generate-mesh --output=apps/journey-realistic/blender/assets/npc-base.blend
python devtools/run.py npc_pipeline rig --input=apps/journey-realistic/blender/assets/npc-base.blend --output=apps/journey-realistic/blender/assets/npc-rigged.blend
python devtools/run.py npc_pipeline export --input=apps/journey-realistic/blender/assets/npc-rigged.blend --output=apps/journey-realistic/public/models/npc-base.glb

# 4. Smoke visual + medición de performance (Playwright headless)
python tmp/journey-realistic-smoke-npc.py   # patrón adaptado de tmp/journey-smoke-perf.py

# 5. Confirmar que apps/journey (la original) sigue intacta
git diff --stat -- apps/journey/   # vacío
pnpm --filter @portfolio/journey run build   # sigue funcionando igual que antes
```

### Medición de performance (AC-8) — resultado real

Medido con `tmp/journey-realistic-smoke-npc.py` contra la sala `aula`
(1 NPC realista MPFB2+Rigify visible + `OutlinePass` activo + resto de
la sala procedural — desktop 1280x800 DPR1 y móvil emulado 390x844 DPR2,
swiftshader software renderer vía Playwright/Chromium). `renderer.info`
requirió `autoReset=false` + reset manual una vez por frame (ver hallazgo
en `mpfb2-api-discovery.md`) para contar correctamente los 3 passes
internos del composer (`RenderPass`+`OutlinePass`+`OutputPass`).

| Métrica | Desktop (1280x800) | Móvil emulado (390x844 DPR2) |
| --- | --- | --- |
| `renderer.info.render.calls` | 184 | 158 |
| `renderer.info.render.triangles` | 96 492 | 41 280 |
| Memoria (geometrías) | 44 | 30 |
| Memoria (texturas) | 41 | 28 |
| Tamaño de `npc-base.glb` en disco | 1.4 MB (Meshopt, idle+walk embebidos) | — |
| Vértices/triángulos del NPC (gltf-transform inspect) | 26 756 vértices / 14 517 triángulos | — |

**Presupuesto de sala propuesto para `apps/journey-realistic`**: con 1 NPC
realista + `OutlinePass` el total ronda ~185 draw calls / ~96K triángulos
en desktop (vs. el `<100` de `journey-rooms.md` para `apps/journey`, que
NO tiene SkinnedMesh ni composer de post-proceso). Presupuesto propuesto
para esta app experimental: **<250 draw calls/sala con hasta 2 NPCs
realistas simultáneos** (el composer de `OutlinePass` es fijo — 3 passes
por frame — independiente del número de NPCs contorneados; el costo
marginal por NPC adicional es ~15K vértices/~145 draw calls extra según
esta medición de 1 NPC). No extrapolado más allá de 2 NPCs: no medido.

**Hallazgo no anticipado**: `OutlinePass` compone el contorno con
`AdditiveBlending` — un ink oscuro (`#141018`, el de `toon.ts`) es
invisible ahí sin importar `edgeStrength`. El contorno real usado es un
glow claro (`#f5f2ea`), NO el ink manga exacto del resto de la sala —
ver el hallazgo completo en `mpfb2-api-discovery.md`.

## Parte C — Verificación de despliegue REAL

**N/A — este plan NO despliega nada** (decisión 12 del README).
`apps/journey-realistic` no se conecta a Cloudflare Pages, no gana
subdominio, no entra al matrix de `deploy-apps.yml`. Es un banco de
pruebas local. La verificación de cierre es local: `pnpm --filter
@portfolio/journey-realistic run dev` sirviendo correctamente en
`localhost:4328` (o el puerto asignado en T1).

## 12. Validación y Definition of Done

### Pre-implementación

- [ ] Los 12 AC están numerados y referenciados por tareas (sección 06)
- [ ] Blender >=4.2 instalado localmente (T3, precondición manual)
- [ ] MPFB2 zip descargado y ubicado en `devtools/npc_pipeline/vendor/`
- [ ] `pnpm install` sin warnings en el monorepo tras agregar
      `apps/journey-realistic`
- [ ] Rama de trabajo creada desde `dev` (`feature/journey-npc-realism`
      o similar) antes de tocar código — la rama actual
      (`feature/journey-puerta-sillas-pilar`) es de un plan distinto

### Definition of Done

- [x] AC-1 a AC-8, AC-10 y AC-11 verificados con comando/evidencia
      reproducible (ver Parte B) — AC-6 con el alcance real documentado
      abajo (no un swap total de `character.ts`, ver nota)
- [ ] AC-9 y AC-12 confirmados por el dueño del proyecto (validación
      humana, T13) — pendiente: el dueño corre
      `pnpm --filter @portfolio/journey-realistic run dev` y compara
- [x] `devtools/npc_pipeline` con coverage >= 80% per-file (39 tests,
      todos verdes; suite completa de devtools: 6 fallos pre-existentes
      sin relación — cloudflare_setup/email_seed/sync_secrets, no
      tocados por este plan)
- [x] Typecheck (`astro check` + `tsc --noEmit`) y Biome pasan en
      `apps/journey-realistic`
- [x] Build estático de `apps/journey-realistic` exitoso
- [x] `apps/journey` (la app original) permanece sin ningún cambio
- [x] Presupuesto de draw calls/sala nuevo documentado con números
      reales (no inventados) — ver tabla arriba
- [x] Licencias de MPFB2/Rigify/glTF-Transform documentadas con fuente
      (ver `.claude/docs/journey-npc-realism/`)
- [ ] Sin push, sin PR, sin deploy — todo local (decisión 11 del
      README); el dueño prueba con
      `pnpm --filter @portfolio/journey-realistic run dev` antes de
      decidir los próximos pasos (push/PR, deploy, o iniciar el plan de
      Etapa 2 — textura painterly)

### Nota sobre el alcance real de AC-6 (T9)

El plan original (sección 8, T9) proponía reescribir `character.ts`
completo para que TODO NPC de la app cargue el `.glb` con la MISMA
interfaz pública. En la práctica, Etapa 1 solo generó 2 clips
(`idle`/`walk`) — las poses `fight`/`sit`/`kneel`/`wave`/`talk` no
existen todavía como `AnimationClip`. Reemplazar `makeCharacter`/
`makeNpc` por completo hoy degradaría a idle/walk TODOS los NPCs
sentados/conversables de las 10 salas (regresión visual amplia, fuera
del scope de una prueba de concepto).

Decisión tomada durante la implementación: se agregó
`spawnRealisticNpc(opts): NpcHandle` en `npc-gltf-loader.ts` —
**mismo contrato `NpcHandle`** que `makeNpc` (`group`/`update`/
`collider`/`talk`/`endTalk`/`jump`/`dispose`), pero respaldado por el
`.glb` real. Se usó para reemplazar **un solo NPC** en `aula.ts`
(`estudianteRonda`, el único que solo usa patrulla + idle/walk, sin pose
fija ni acciones sin clip) — visible y comparable en vivo junto a los
NPCs procedurales, sin tocar `dialog.ts` ni `hud.ts`. Un swap total de
`character.ts` (el T9 tal como se escribió) requeriría primero generar
los 5 clips restantes — trabajo de una pasada siguiente, no de esta.
