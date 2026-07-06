# 9. Commits

Commits incrementales para cuando se implemente este plan. Cada uno deja
el repo verde (typecheck + Biome; build al final). El primero es la
carpeta del plan; el último es el de la sección 11 (incluye el `git rm
-r` de la carpeta del plan). Un solo PR
`feature/journey-puerta-sillas-pilar -> dev` (o la rama de trabajo que
esté activa al momento de implementar — ver
[10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md)).

1. `docs(specs): agrega plan journey-puerta-sillas-pilar`
   - Agrega la carpeta completa del plan (este documento).
   - Verificación: N/A (solo documentación).

2. `feat(journey): estado playerSeat para sentarse en sillas vacias`
   - T1: `engine/state.ts` — `SeatTarget` + `EngineState.playerSeat`.
   - AC: base de AC-1, AC-2, AC-5 (el campo, sin uso todavía).
   - Verificación: `astro check`.

3. `feat(journey): officeLayout expone sillas vacias sentables`
   - T2 (parte 1 de 3): `props.ts` — `officeLayout` gana `seats`.
   - AC: AC-1, AC-3.
   - Verificación: `astro check` + Biome.

4. `fix(journey): centra el pilar del cuaderno y gira el libro de frente`
   - T2 (parte 2 de 3): `props.ts` — `infoKit`/`lecternNotebook`.
   - AC: AC-6, AC-7, AC-8, AC-9.
   - Verificación: `astro check` + smoke visual en `aula`.

5. `fix(journey): corrige el contorno de tinta de los cuadros (wallArt)`
   - T2 (parte 3 de 3): `props.ts` — `wallArt` con `outlinedMergedBoxes`.
   - AC: AC-10.
   - Verificación: `astro check` + smoke visual + draw calls.

6. `feat(journey): el jugador se sienta y levanta con E`
   - T3: `controls.ts` — congela movimiento y aplica pose sentado.
   - AC: AC-1, AC-2, AC-5 (cierra el ciclo).
   - Verificación: `astro check` + smoke (sentarse/levantarse).

7. `feat(journey): sillas vacias sentables en las 9 salas de oficina`
   - T4: los 9 archivos de sala (cofasa, corpoelec, ipasme, iai,
     asesoria, goodmeal, dibal, destacame, futuro).
   - AC: AC-1, AC-3.
   - Verificación: `astro check` + smoke en 2 salas.

8. `feat(journey): sillas vacias sentables en el aula`
   - T5: `aula.ts`.
   - AC: AC-4.
   - Verificación: `astro check` + smoke en `aula`.

9. `feat(journey): puerta con cruce automatico y efecto viaje al futuro`
   - T6: `world.ts` (`buildCorridorShell` reducido + `crossDoor`) +
     `hud.ts` (`fade('warp')`).
   - AC: AC-11, AC-12, AC-13, AC-14.
   - Verificación: `astro check` + smoke de 2 cruces de puerta.

10. `docs(specs): cierra plan journey-puerta-sillas-pilar`
    - Sección 11 completa (Partes A y B en verde).
    - `git rm -r docs/specs/journey-puerta-sillas-pilar/`.
    - Verificación: batería completa de
      [11-verificacion-e2e.md](11-verificacion-e2e.md).

> Nota (decisión de ejecución, ver README): tras el commit 9 y la
> verificación local en verde, se PAUSA antes de `git push`/PR — el
> usuario prueba primero con `pnpm --filter @portfolio/journey dev`. El
> commit 10 (cierre) y el push/PR ocurren solo tras su confirmación.
