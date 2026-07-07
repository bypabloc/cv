# Plan: puerta sin túnel, sentarse en sillas vacías, pilar centrado y libro con estilo

> Cuatro correcciones/mejoras puntuales sobre `apps/journey` (el CV como
> viaje 3D), reportadas tras probar visualmente las 10 salas del plan
> `journey-cuaderno-central` recién cerrado: (1) el jugador no puede
> sentarse en sillas vacías, (2) el pilar del cuaderno-reseña del aula no
> está en el centro de la sala y el libro muestra el reverso, (3) el
> contorno de tinta de los cuadros (`wallArt`) se sale del marco en
> ciertos ángulos, (4) el túnel/pasillo entre salas tiene un techo
> discontinuo y barras laterales mal puestas, y debería ser solo una
> puerta que teletransporta automáticamente a la sala siguiente con un
> efecto de "viaje al futuro".

## Cuando leer cada archivo

| Archivo | Cuando leer |
|---------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Contexto de las 4 fallas, decisión general y los 14 criterios de aceptación (AC-1 a AC-14) |
| [02-feature-sillas-vacias.md](02-feature-sillas-vacias.md) | Diseño de la mecánica "sentarse en cualquier silla vacía" (estado del jugador, `officeLayout`, aula) |
| [03-feature-aula-pilar-libro.md](03-feature-aula-pilar-libro.md) | Reposicionar el pilar al centro real de la sala + girar y rediseñar el libro con volumen |
| [04-feature-ficha-contorno.md](04-feature-ficha-contorno.md) | Fix del contorno de tinta de `wallArt` (marco `mergedBoxes` → `outlinedMergedBoxes`) |
| [05-feature-puerta-sin-tunel.md](05-feature-puerta-sin-tunel.md) | Reemplazo del pasillo por una puerta con cruce automático + efecto "viaje al futuro" |
| [06-tests-requeridos.md](06-tests-requeridos.md) | Qué se verifica de cada feature (journey está exenta de tests unit — ver rule `astro-landing.md`) |
| [07-archivos-afectados.md](07-archivos-afectados.md) | Listado completo de archivos a tocar, con su verificación puntual |
| [08-descomposicion.md](08-descomposicion.md) | Tareas atómicas y qué se puede paralelizar |
| [09-commits.md](09-commits.md) | Commits incrementales planeados |
| [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md) | Uso de git worktrees para las tareas paralelizables |
| [11-verificacion-e2e.md](11-verificacion-e2e.md) | Batería de verificación final + Definition of Done |

## Estado

| Fase | Estado |
|------|--------|
| Spec creado | Hecho (este documento) |
| Implementación | Pendiente |

## Decisiones no reabribles

1. **`apps/journey` está exenta de tests unit** (PR #306, ver
   `.claude/rules/astro-landing.md` cross-ref en `journey-rooms.md`): la
   verificación de este plan es typecheck + Biome + build + smoke visual
   (headless/headed), NUNCA Vitest.
2. **No se toca `lib/layout.ts` ni el tipo `Zone`/`corridor`**: se
   mantiene el modelo de datos del pasillo (para no tocar la lógica de
   esclusa/preload, el riel del tour guiado y el colisionador de puerta
   cerrada), y solo se deja de RENDERIZAR su geometría visual y de
   CAMINARLO — el cruce pasa a ser un teletransporte automático al abrir
   la puerta. Ver decisión completa en
   [05-feature-puerta-sin-tunel.md](05-feature-puerta-sin-tunel.md).
3. **Sin librería nueva ni asset de audio nuevo**: el efecto "viaje al
   futuro" reusa el mecanismo de fade existente (`hud.fade`) + los SFX
   procedurales ya disponibles (`door`, `whoosh`), agregando solo una
   variante CSS de fade nueva.
4. **local-first**: al terminar la implementación y la verificación local
   (batería de la sección 11, Partes A y B), NO se hace push ni se abre
   PR automáticamente. Se dejan los commits locales y se le indica al
   usuario el comando `pnpm --filter @portfolio/journey dev` para que
   pruebe primero en el navegador — coherente con la preferencia ya
   registrada en memoria (`journey-local-first-workflow`). El push/PR se
   hace solo cuando el usuario confirma.

## Reglas críticas aplicables

- `.claude/rules/journey-rooms.md` — canon de sala (helpers, paredes
  blancas, <100 draw calls, los 4 puntos de infra).
- `.claude/rules/typescript.md` — TS 6 strict, sin `any`.
- `.claude/rules/verify-before-done.md` — no declarar listo sin verificar.
- `.claude/rules/orchestration.md` — máx. 4 agentes concurrentes, 1
  workflow a la vez, si se usan subagentes para las tareas paralelizables.

## Navegación

Empezar por [01-contexto-y-decision.md](01-contexto-y-decision.md).
