# Estado activo — feature/journey-npc-realism

> Sesión en curso. Retomar leyendo este archivo completo antes de tocar
> nada. Última actualización: 2026-07-07.

## Qué es esta rama

Plan `docs/specs/journey-npc-realism/` — reemplazar los NPCs procedurales
de `apps/journey` (descritos por el dueño como "robóticos y horribles")
por humanoides `.glb` riggeados (Blender headless: MPFB2 + Rigify +
keyframing + glTF-Transform), en una app nueva `apps/journey-realistic`
que NO toca `apps/journey` en producción.

## Estado por etapa

| Etapa | Estado | Dónde vive |
|---|---|---|
| **Etapa 1** (geometría/rig/silueta + animación esquelética) | **Commiteada** (T1-T12, 3 commits: `7886a1b5` plan, `40c7ca12` scaffold app, `ccb06273` devtools `npc_pipeline`). T13 (validación visual del dueño) **pendiente** — local-first, sin push/PR/deploy hasta confirmar en `pnpm --filter @portfolio/journey-realistic run dev` | `apps/journey-realistic/`, `devtools/npc_pipeline/` |
| **Etapa 2** (textura painterly) | **Exploración en curso, SIN commitear** — 3 rondas de comparación de estilos ya hechas, sin tocar código de `apps/journey-realistic` todavía | `tmp/npc-style-variants/` (ver abajo) |

Etapa 2 **no tiene carpeta de plan propia** todavía (decisión no-reabrible
#2 del README de Etapa 1: es "un plan futuro separado" que arranca recién
cuando el dueño valide Etapa 1). Este documento es el puente hasta que
eso pase.

## Qué se exploró en Etapa 2 (3 rondas)

1. **Ronda 1**: 6 estilos painterly/toon distintos generados con Blender
   headless (materiales por nodos, sin textura pintada real todavía).
2. **Ronda 2**: 3 estilos refinados con research de técnicas reales
   (Puss in Boots: The Last Wish rim-light, Spider-Verse Ben-Day +
   aberración cromática, Caricatura toon flat + stamp). El dueño vio
   capturas y **confirmó estos 3 como favoritos**.
3. **Ronda 3**: a esos 3 favoritos se les agregó:
   - **Rostro** (cejas/ojos/labios) vía máscaras esféricas ancladas al
     centroide de vertex groups deformados (`_compute_face_pivots` en
     `render_variants.py`).
   - **4 outfits** (universitario/oficina/formal/informal) diseñados por
     un workflow de 4 agentes en paralelo investigando moda real, cada
     uno con su paleta de colores propia (`outfit-design-raw.json`).
   - Se re-renderizaron los 3 estilos base + 4 outfits x 3 estilos = 12
     combinaciones nuevas.

## Decisiones tomadas (no reabrir sin razón nueva)

1. **3 estilos ganadores confirmados por el dueño**: Puss in Boots,
   Spider-Verse, Caricatura. Los otros 3 de la Ronda 1 quedan descartados.
2. **Sistema de rostro**: funciona anclando la máscara esférica al
   centroide de vértices deformados de un vertex group (`DEF-eye.L/R`),
   NO a la posición de un hueso (ni bind-pose ni posado) — ambas
   variantes de hueso se probaron y no coincidían con la superficie real
   tras el escalado de proporción.
3. **Freestyle SÍ se usa** para el contorno tipo ink en Toon Ink,
   Spider-Verse y Caricatura. **Freestyle NO se usa** en Puss in
   Boots ni Painterly-Rim (ahí el contorno es rim-light/glow, no línea
   oscura — fiel a la técnica real de la película).
4. **Aberración cromática** (post-proceso Pillow) SOLO en Spider-Verse,
   aplicada a las 5 vistas (base + 4 outfits) x 2 ángulos.

## Bugs y limitaciones conocidas (sin resolver)

| Problema | Estado | Detalle |
|---|---|---|
| Puss in Boots: ojos/cejas no renderizan | **Aceptado como limitación**, no bloqueante | Afecta la proporción `stylized-mild` (escala la cabeza 1.12x). 3 técnicas de pivote probadas (hueso bind-pose, hueso posado, centroide de vértice deformado) — ninguna ubicó la máscara sobre superficie visible, confirmado con renders de cámara cerrada + inspección de píxeles. El pelo y la boca SÍ funcionan con el mismo patrón. Causa raíz no identificada; se documentó y se dejó de iterar tras varios intentos. |
| Pantalón "lavado"/pálido en office y formal (los 3 estilos) | **Detectado, SIN corregir** | Office debería ser casi negro (`0.22,0.23,0.26`) y sale gris-lavanda pálido; formal debería ser azul marino (`0.11,0.16,0.29`) y sale azul medio saturado. Sospecha: el mismo mix de Fresnel/Emission-anchor usado para "despegar" Puss in Boots del look plano está sobre-exponiendo la zona de pantalón en los 3 estilos. Próximo paso al retomar: revisar `_painted_zone_node` en `render_variants.py` y los 3 builders en `render_variants_v2.py`. |
| Corbata (outfit formal) sin forma | Cosmético, no bloqueante | Es una franja recta sin nudo ni angostamiento — se lee como rayón, no corbata. `_stripe_mask` en `render_variants.py` es el punto de partida si se quiere una forma trapezoidal. |
| Tirantes de mochila (outfit universitario) leen como suspensores | Cosmético, no bloqueante | De frente se ven 2 franjas verticales paralelas; en la realidad entran diagonal desde el hombro. |

## Dónde está todo

- **Scripts** (Blender headless, bpy): `tmp/npc-style-variants/*.py` —
  `render_variants.py` (helpers compartidos: pivotes, máscaras, sistema
  de rostro), `render_variants_v2.py` (los 3 builders de estilo
  ganadores), `render_round3_outfits.py` (loop de 4 outfits x 3
  estilos), `build_gallery.py` (arma el HTML de la galería),
  `apply_chromatic_aberration.py` (post-proceso Spider-Verse).
- **Renders**: `tmp/npc-pipeline/style-variants/*.png` (36+ imágenes:
  3 base + 24 de outfits + variantes previas de rondas 1-2).
- **Research de outfits**: `tmp/npc-style-variants/outfit-design-raw.json`
  (las 4 paletas completas con notas y fuentes de cada agente).
- **Galería visual navegable**: Artifact
  `https://claude.ai/code/artifact/0ee6b9e1-21bc-442a-a62b-e094da029839`
  (se redeploya a la MISMA URL en cada actualización — `build_gallery.py`
  seguido de la tool `Artifact`).

### Importante: `tmp/` está gitignored

Todo lo de arriba en `tmp/npc-style-variants/` y
`tmp/npc-pipeline/style-variants/` **NO viaja con git** (regla del
proyecto: temporales siempre en `./tmp/`, nunca commiteados). Este
documento es la única constancia versionada de ese trabajo. Si se pierde
el directorio `tmp/` local (limpieza manual, otra máquina, etc.) hay que
re-generar todo corriendo los scripts de nuevo — no hay forma de
recuperarlo desde git. Si en algún momento se decide que el pipeline de
estilos vale la pena persistir en el repo (no solo como scratch), hay
que moverlo explícitamente a una carpeta trackeada (ej.
`devtools/npc_style_pipeline/` o dentro de la futura carpeta de plan de
Etapa 2) — no se hizo en este commit, quedó fuera de alcance.

## Próximos pasos al retomar

1. Corregir el lavado de color del pantalón en office/formal (ver tabla
   de bugs arriba) antes de mostrar de nuevo la galería.
2. Decidir con el dueño: ¿se acepta la limitación de ojos de Puss in
   Boots, o vale la pena un intento más con otra técnica de pivote?
3. Cuando el dueño elija estilo + outfit definitivo → formalizar como
   plan nuevo `docs/specs/journey-npc-realism-etapa2/` (con sus AC,
   descomposición de tareas, etc. — recién ahí deja de ser exploración
   suelta).
4. Recordar: nada de este trabajo tocó código de `apps/journey-realistic`
   todavía. Sigue siendo 100% exploración en `tmp/` + la galería Artifact.
   Local-first: sin push/PR/deploy de código real hasta que el dueño
   confirme (memoria `journey-local-first-workflow`).
