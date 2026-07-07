# 11. Verificación E2E iterativa (fase final)

## Parte A — refactor de tests

`apps/journey` está exenta de tests unit (decisión heredada, ver PR #306
referenciado en `astro-landing.md`) — no hay suite Vitest que migrar.
Verificar igual:

```bash
rg -l "inverted-hull|outlineGroup|toonMat" apps/journey/src/engine/rooms/{aula,futuro,destacame}.ts
# esperado: 0 resultados tras T4a-T4c (esos helpers ya no se usan en las
# 3 salas migradas; SÍ pueden seguir apareciendo en las 7 salas no
# tocadas y en toon.ts, eso es correcto)
```

## Parte B — batería de comandos reales

```bash
pnpm exec biome check apps/journey
pnpm exec tsc --noEmit
pnpm --filter @portfolio/journey exec astro check
pnpm --filter @portfolio/journey run build
pnpm --filter @portfolio/journey run preview &
# confirmar CSP: dist/_headers contiene worker-src con blob:
rg "worker-src" apps/journey/dist/_headers
```

Bucle "no parar hasta que funcione": si algo falla, diagnosticar,
corregir, re-ejecutar la suite completa, repetir.

## Parte C — verificación visual manual (reemplaza E2E automatizado —
es un cambio 100% visual, sin flujo nuevo de negocio que testear con
Playwright)

```bash
pnpm --filter @portfolio/journey run dev
```

Checklist manual en el browser:

- [ ] Sala `aula`: mobiliario CC0 visible, halftone+contorno+aberración
      aplicados, NPCs (`companeraLab`, `estudianteSockets`,
      `estudianteRonda`) animan y hablan al acercarse (E).
- [ ] Ficha RETOS/APRENDIZAJES abre como panel DOM (no textura).
- [ ] Grieta al pasado (portal) sigue cruzando a la sala sepia de aula.
- [ ] Cruce por pasillo aula → futuro sin bloqueos de colisión extraños.
- [ ] Sala `futuro`: `futurePortal` shader (vórtice/rayos) sigue
      funcionando; props sci-fi CC0 visibles con el estilo nuevo.
- [ ] Cruce por pasillo futuro → destacame.
- [ ] Sala `destacame`: 2 showcases (`showcaseA`/`showcaseB`) abren panel
      DOM operable con E; mobiliario de oficina CC0 visible.
- [ ] Jugador (personaje CC0) camina, corre animación de walk/idle
      correctamente, contorno de tinta visible durante el movimiento.
- [ ] Sin errores de consola (CSP de Workers Draco/KTX2, 404 de assets).
- [ ] `renderer.info.render.calls` (consola DEV, `__journeyDebug.info`)
      registrado como dato informativo — sin gate, sin bloquear (decisión
      no-reabrible 4).

## Definition of Done

- [ ] Los 9 AC (01-contexto-y-decision.md) tienen evidencia de
      cumplimiento (visual o de comando).
- [ ] Biome + `tsc --noEmit` + `astro check` en verde.
- [ ] Build + preview exitosos, CSP con `worker-src` confirmada.
- [ ] `CREDITS.md` completo (T5).
- [ ] Checklist visual de la Parte C completo.
- [ ] **Sin push/PR/deploy** — el dueño confirma primero en
      `pnpm --filter @portfolio/journey run dev` (AC-9, decisión
      no-reabrible 6). Recién con su confirmación explícita se decide el
      siguiente paso (push/PR, o más iteración visual).
- [ ] Este commit incluye `git rm -r docs/specs/journey-spiderverse-style/`
      SOLO si el dueño da por cerrado el prototipo — si pide más
      iteración, la carpeta del plan permanece.
