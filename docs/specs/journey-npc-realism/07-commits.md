# 9. Commits

10 commits incrementales. Cada uno deja el repo verde (lint + typecheck
+ build del scope tocado). Un solo PR eventual
`feature/journey-npc-realism -> dev` (que NO se abre en este plan — ver
decisión 11 del README, local-first).

1. `docs(specs): plan journey-npc-realism` — la carpeta de este plan
   (ya redactada). Verificación: ninguna (solo docs).
2. `feat(journey-realistic): scaffold de app nueva copia de journey`
   (T1) — AC-1. Verificación:
   `pnpm --filter @portfolio/journey-realistic run build`.
3. `chore(devtools): scaffold de npc_pipeline (orquestacion + tests)`
   (T2) — AC-11 (parcial). Verificación:
   `python devtools/run.py test_runner --module=devtools --type=unit`.
4. `feat(npc-pipeline): install_addons.py + api-discovery de MPFB2`
   (T4, tras el setup manual T3) — precondición AC-2. Verificación:
   script corre headless sin excepciones + doc de API completo.
5. `feat(npc-pipeline): generate_mesh.py (malla base humanoide MPFB2)`
   (T5) — AC-2. Verificación: preview PNG revisado, silueta aprobada.
6. `feat(npc-pipeline): rig_mesh.py (rig Rigify + validacion de piel)`
   (T6) — AC-3. Verificación: preview de pose de prueba sin artefactos.
7. `feat(journey-realistic): export .glb + carga GLTFLoader/AnimationMixer`
   (T7 animación manual + T8 export + T9 `character.ts`, combinados
   porque es la primera vez que el `.glb` final y el nuevo `character.ts`
   se verifican juntos) — AC-4, AC-5, AC-6. Verificación: `astro check` +
   smoke visual con animación corriendo, `rooms/`/`dialog.ts`/`hud.ts`
   sin cambios.
8. `feat(journey-realistic): OutlinePass para NPCs humanoides` (T10) —
   AC-7. Verificación: smoke visual, contorno correcto durante animación.
9. `docs(specs): medicion de performance + licencias documentadas`
   (T11 + T12) — AC-8, AC-10. Verificación: 4 números de performance
   documentados + licencias con fuente.
10. `docs(specs): cierre del plan journey-npc-realism` (T13 + sección 11
    completa) — AC-9, AC-12. Verificación: batería completa de la
    sección 09-verificacion-e2e.md en verde. **Sin push/PR** (decisión
    11 del README) — el commit queda local; se comunica al dueño el
    comando `pnpm --filter @portfolio/journey-realistic run dev` para
    probar antes de decidir push/PR/deploy o Etapa 2.
