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

## Addendum 2026-07-07 — giro de dirección visual + restyle

Tras validar el prototipo en su GPU, el dueño pidió cambios que **revierten
parte del look Spider-Verse** y refinan el aula. Estos reemplazan a los AC-3
y AC-4 originales (que exigían halftone + contorno de tinta):

1. **Se elimina TODO el post-procesado cómico** (contornos inverted-hull en
   personajes/props + halftone Ben-Day + aberración cromática). Motivo:
   gasta recursos y "no tiene buen acabado". El render pasa a **3D toon
   limpio, directo** (sin `EffectComposer`), con MSAA nativo. Aplica a las
   10 salas (no solo las 3 prototipo). `postfx.ts` se borra;
   `toon.ts::outlineGroup`/`outlinedMergedBoxes` quedan sin contorno.
   → commit `4c8b3add`.
2. **Fix del caminar del jugador**: `setWalking`/`setPose` re-disparaban el
   clip cada frame (`playClip` → `reset()`), congelando la animación Walk al
   mantener la tecla. Guard: solo re-dispara al CAMBIAR de pose. → `4c8b3add`.
3. **Aula = colegio de bajos recursos**: mobiliario a **madera**, monitores
   **CRT blancos/crema** (estilo 2000), y las **3 pizarras** del muro pasan a
   **pizarra verde vieja con marco de madera** (tiza sobre verde). → `d7fcb8e8`.
4. **futuro Plan A**: estaciones de trabajo **sci-fi CC0** (Kenney Space
   Station Kit), con `toonifyFurniture` que **preserva la textura** del pack.
   → `a2a62729`.

Pendiente de conversación con el dueño (no bloqueante): la firma sonora por
rubro y el resto de props del futuro (computer.glb del pack sci-fi está
vendorizado pero sin colocar aún); si quiere, las pizarras RETOS/APRENDIZAJES
(infoKit, hoy navy) también podrían ir a verde.

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
