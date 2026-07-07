# Plan: estilo Spider-Verse en `apps/journey` (prototipo 3 salas)

> Reemplaza el estilo manga-ink procedural de `aula`, `futuro` y
> `destacame` (más el sistema de personajes completo) por un look
> cel-shaded/halftone estilo "Into the Spider-Verse", usando assets 3D
> reales CC0 (Kenney, Quaternius, Mixamo) en vez de geometría procedural.
> Prototipo acotado a 3 salas — generalizar a las 10 es un plan futuro
> separado. Local-first: sin push/PR/deploy hasta validación visual del
> dueño.

## Cuando leer cada archivo

| Archivo | Cuando leer |
|---------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Contexto completo, decisiones no-reabribles (incluye el hallazgo de la rama huérfana `feature/journey-npc-realism`) y los 9 criterios de aceptación |
| [02-arquitectura-tecnica.md](02-arquitectura-tecnica.md) | Qué sistemas del engine se tocan vs no, el pipeline de carga GLTF/Draco/KTX2, el pipeline de postprocesado (halftone/aberración/outline) |
| [03-sourcing-assets.md](03-sourcing-assets.md) | Los packs CC0 elegidos, licencias, y el pack sci-fi pendiente de confirmar |
| [04-archivos-afectados.md](04-archivos-afectados.md) | Listado de archivos crear/modificar/NO tocar, con verificación por archivo |
| [05-riesgos-y-decisiones-abiertas.md](05-riesgos-y-decisiones-abiertas.md) | 5 riesgos identificados que se resuelven durante la implementación |
| [06-descomposicion-tareas.md](06-descomposicion-tareas.md) | Tareas atómicas T1-T8, AC referenciados, paralelizabilidad |
| [07-commits.md](07-commits.md) | Commits incrementales planeados |
| [08-paralelizacion-worktrees.md](08-paralelizacion-worktrees.md) | Base secuencial (T1-T3) + olas de worktrees (T4a-T4c) |
| [09-verificacion-e2e.md](09-verificacion-e2e.md) | Batería de verificación final + Definition of Done |

## Estado

| Fase | Estado |
|------|--------|
| Investigación (bundle de Messenger, packs CC0, shader Spider-Verse) | Hecho |
| Descubrimiento de `feature/journey-npc-realism` (rama huérfana) | Hecho — no se retoma, ver decisión no-reabrible en 01 |
| Spec/plan creado | Hecho (este documento) |
| Implementación (T1-T8) | En curso |

## Decisiones no reabribles (resumen — detalle en 01)

1. Reemplazo total del manga-ink en las 3 salas prototipo (no evolución).
2. Assets 100% CC0 descargados — NO se reusa el pipeline Blender/MPFB2 de
   `feature/journey-npc-realism`.
3. Sin límite fijo de draw calls en este plan.
4. Personajes (jugador + NPCs) migran también.
5. Reemplaza `apps/journey` directamente (sin app sandbox) — mitigado con
   local-first (sin push/PR/deploy hasta validación visual).
6. Alcance: `aula`, `futuro`, `destacame` únicamente.
7. El shell de sala (`world.ts::buildRoomShell`, compartido por las 10
   salas) NO se toca — solo el contenido interior de las 3 prototipo.

## Reglas críticas

- El contrato `RoomFactory = (ctx) => RoomBuild` (`world.ts`) y
  `CharacterHandle`/`NpcHandle` (`character.ts`) se preservan — ver
  [02-arquitectura-tecnica.md](02-arquitectura-tecnica.md).
- `lib/layout.ts`, `lib/rooms.ts`, `lib/collision.ts`, `controls.ts`,
  `hud.ts`, `dialog.ts` NO se tocan (ver 02).
- El texto del CV sigue siendo HTML real en el DOM — NUNCA WebGL (AC-7,
  regla dura heredada de `.claude/rules/journey-rooms.md`).
- Local-first: commits quedan en la rama local `feature/journey-spiderverse-style`.
  Sin push/PR/deploy hasta que el dueño confirme en
  `pnpm --filter @portfolio/journey run dev`.

## Referencias

- [.claude/rules/journey-rooms.md](../../../.claude/rules/journey-rooms.md)
  — canon manga-ink vigente para las 7 salas NO tocadas en este plan.
- [.claude/rules/plan-format.md](../../../.claude/rules/plan-format.md) —
  formato de este documento.
- Rama huérfana de referencia (NO se retoma):
  `feature/journey-npc-realism` — `docs/specs/journey-npc-realism/` en
  esa rama documenta un pipeline Blender/MPFB2/Rigify alternativo y una
  exploración de 5 estilos NPC (3 confirmados: Puss in Boots, Spider-Verse,
  Caricatura) que puede servir de referencia visual, aunque este plan no
  reutiliza su código.
