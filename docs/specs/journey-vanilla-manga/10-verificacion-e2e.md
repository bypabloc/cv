# 10 — Seccion 11: verificacion E2E iterativa + seccion 12: DoD

> Fase final y ULTIMO commit (C8). Bucle: ejecutar → si falla, diagnosticar
> → corregir → re-ejecutar TODO → repetir. El push y el PR ocurren SOLO con
> las Partes A y B en verde. La Parte C corre tras el merge/deploy.

## Parte A — refactor de tests y restos

Journey no tiene suite unit (exento), asi que la Parte A es el barrido de
RESTOS del codigo eliminado (cero resultados esperados en todos):

```bash
rg -l "react|react-dom|@react-three|troika|zustand" apps/journey/src
rg -l "components/three|Journey3D|useJourneyStore" apps/journey
rg -l "space-grotesk-latin-400" apps/journey
rg -l "@astrojs/react" apps/journey
rg -n "journey" .git-hooks/ devtools/test_runner/ 2>/dev/null   # sin refs nuevas
```

Ademas: `apps/journey/tests/` y `vitest.config.ts` no existen;
`package.json` sin scripts `test*` ni deps react/vitest.

## Parte B — bateria de comandos reales (gate del push/PR)

```bash
# 1. install limpio (lockfile actualizado, sin peer warnings)
pnpm install

# 2. lint global
pnpm run lint

# 3. typecheck del app
pnpm --filter @portfolio/journey run typecheck

# 4. build (genera dist con chunk 3D separado)
pnpm --filter @portfolio/journey run build

# 5. cero React en el bundle (AC-12)
rg -l "react" apps/journey/dist/_astro --iglob '*.js' | head   # esperado: 0
ls apps/journey/dist/index.html                                 # fallback 2D presente
rg -c "cv-fallback" apps/journey/dist/index.html                # >= 1

# 6. typecheck + build del RESTO del monorepo (nada se rompio)
pnpm run typecheck
pnpm run build

# 7. dev server + smoke HTTP
pnpm --filter @portfolio/journey dev &   # puerto 4327
curl -fsS http://localhost:4327/ | rg -c "journey-root|cv-fallback"  # ambos
curl -fsS http://localhost:4327/en/ | rg -c 'data-locale="en"'
```

### Verificacion manual en browser (obligatoria antes del push)

Checklist sobre `http://localhost:4327/`:

- [ ] Loader "Cargando el mundo 3D…" aparece y DESAPARECE (AC-1)
- [ ] 3a persona default: personaje visible, drag gira camara, WASD camina
      relativo a la camara (AC-5)
- [ ] V alterna a POV (pointer-lock, personaje oculto) y de vuelta (AC-5)
- [ ] Estetica manga-ink: colores planos, escalones de luz duros, contornos
      negros en personajes/props, screentone sutil (AC-6)
- [ ] NPCs distinguibles con caras y parpadeo; patrullas activas (AC-7)
- [ ] Recorrido completo aula → corpoelec → cima abriendo puertas con E;
      al entrar a cada pasillo la sala anterior se libera: en consola
      (DEV) `renderer.info.memory` vuelve al nivel base al alternar salas
      ida y vuelta (AC-3) y `render.calls < 100` por zona (AC-10/AC-14)
- [ ] Volver hacia atras reconstruye la sala previa con fade, nunca sala
      vacia (AC-4)
- [ ] Fichas retos/aprendizajes abren panel DOM legible; micro-interaccion
      de cada sala responde; portal al pasado aplica sepia y retorna;
      CTA contacto abre panel con links; M abre teletransporte y salta con
      fade; audio opt-in suena por sala (AC-9)
- [ ] `/en/` muestra HUD y textos en ingles (AC-11)
- [ ] DevTools device emulation (movil): joystick + boton E + drag camara
      + boton Tour recorren el riel con textos; sin sombras dinamicas
      (AC-8)
- [ ] "Ver CV 2D" sale al fallback y el boton "Explorar en 3D" re-entra

## Parte C — verificacion de despliegue REAL (post-merge)

Tras mergear el PR a `dev` (dispara `deploy-apps.yml`):

```bash
# 1. resultado del workflow (conclusion global + CADA job)
gh run list --workflow=deploy-apps.yml --branch=dev --limit=1 \
  --json databaseId,conclusion,status
gh run view <id> --json jobs --jq '.jobs[] | {name, conclusion}'

# 2. curl a la URL canonica
curl -fsS -o /dev/null -w "HTTP %{http_code}\n" --max-time 25 \
  https://journey.portfolio.dev.the-full-stack.com/

# 3. E2E app contra dev desplegado (incluye test_journey_3d_mounts)
python devtools/run.py e2e --module=app --env=dev
```

El plan NO se declara listo sin: workflow verde (todos los jobs), HTTP 200
en la URL real y el E2E app en verde. Promocion a prod (`dev -> main`)
repite el curl contra `https://journey.portfolio.the-full-stack.com/`.

## 12. Validacion y Definition of Done

### Pre-implementacion

- [ ] Decisiones del usuario registradas (README) y AC numerados
- [ ] Rama `refactor/journey-vanilla-manga` creada desde `dev`
- [ ] `pnpm install` verde y dev server actual arranca (linea base)
- [ ] Contratos (RoomCtx/RoomBuild/CharacterHandle/Hud/EngineState)
      congelados antes de cualquier fan-out

### Definition of Done

- [ ] AC-1..AC-14 verificados (matriz de la Parte B + C)
- [ ] Parte A: cero restos de React/R3F/troika/zustand
- [ ] Parte B completa en verde (install/lint/typecheck/build/manual)
- [ ] PR `refactor/journey-vanilla-manga -> dev` mergeado con merge commit
- [ ] Parte C: workflow verde + HTTP 200 + E2E app verde
- [ ] Carpetas `docs/specs/journey-vanilla-manga/` y
      `docs/specs/journey-3d-cv/` eliminadas (C8 / commit de limpieza)
- [ ] Verificacion visual final del usuario (estetica manga-ink aprobada)
