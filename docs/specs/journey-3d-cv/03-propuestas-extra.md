# Propuestas extra (C-F) — variantes investigadas

> [<- Propuesta B (scroll)](02-propuesta-b-scroll-journey.md) · [Siguiente: arquitectura ->](04-arquitectura-comun.md)

Ademas de A (habitaciones), B (scroll) y G (POV mundo libre), el research
produjo 4 escenarios mas. Cada uno
es una metafora distinta para los mismos datos (13 anos, intern->lead). El eje
protagonista sigue siendo la **progresion profesional/seniority**; la geografia
es guiño. Ordenados por relacion valor/esfuerzo.

> Nota: la Propuesta C (globo/mapa) es la unica intrinsecamente geografica.
> Se mantiene como OPCION por su claridad y fallback, pero dado que el usuario
> descarto la geografia como foco, es una variante secundaria, NO recomendada
> como #1. Si se usa, debe encuadrar el mapa como "trabajo remoto para clientes
> LATAM" (un plus profesional), no como historia de migracion.

## Propuesta C — Globo / mapa del mundo con 3 ciudades (MEJOR MVP alternativo)

Un globo/mapa LATAM estilizado con **Lima** como base (residencia) y pines a
los mercados donde trabajaste remoto (Peru, Chile, Mexico). Encuadre correcto:
NO es un mapa de migracion, es un mapa de **alcance profesional remoto**. Zoom
a cada mercado -> mini-escena 3D con los proyectos de ese cliente.

- **Mapeo**: mercado del cliente = pin (alcance remoto LATAM, un plus
  profesional), ano = orden de conexion, seniority = tamaño/altura del pin.
- **Nav**: orbit + click-to-fly a cada nodo; dentro de cada mercado, tour de
  puntos fijos. Sin physics.
- **Pros**: instantaneamente legible (todos entienden un mapa); "trabajo remoto
  para multiples mercados LATAM" es un plus real; barato (sin free-roam);
  bueno para GEO/SEO (mercados enlazables); fallback movil = el mapa mismo.
- **Contras**: es intrinsecamente geografico -> choca con "el foco NO es la
  geografia". Solo usar si se encuadra como alcance remoto, NUNCA como
  migracion. Menos "POV inmersivo" (es orbital).
- **Esfuerzo**: medio. Riesgo bajo tecnico, pero riesgo NARRATIVO (desalinea
  con el eje profesional). Variante secundaria, NO la #1.

## Propuesta D — Museo / galeria de salas (MVP tecnicamente mas seguro)

Un museo caminable en primera persona; cada sala = un pais o etapa (intern room,
mid room, senior room, lead room). Los proyectos son cuadros/vitrinas; al
acercarte se abre la ficha del CV.

- **Mapeo**: etapa/nivel de carrera = sala, proyecto = obra en la pared,
  seniority = progresion de salas (mas grandes/opulentas al avanzar).
- **Nav**: first-person WASD + mouse-look (`PointerLockControls`). Es el POV
  mas "puro".
- **Pros**: first-person genuino con el **menor riesgo tecnico** — salas
  cerradas = colisiones caja triviales (sin heightmap ni navmesh); precedente
  open-source directo (Virtual-art-gallery); interaccion "acercarse a cuadro
  -> ficha" es la mas limpia.
- **Contras**: metafora menos original (muchos museos 3D); salas neutras/
  uniformes (menos caracter que la G, que ambienta cada sala por epoca).
- **Esfuerzo**: bajo-medio. **Riesgo bajo-medio.** Es el MVP tecnico mas seguro
  si se quiere first-person real sin la complejidad de G.

> **Ver Propuesta A** ([01-propuesta-a-habitaciones.md](01-propuesta-a-habitaciones.md)):
> es la version "juego inmersivo" de esta idea — habitaciones AMBIENTADAS por
> epoca/logro, conectadas por puertas con ida y vuelta, en vez de un museo
> neutro. La pidio el usuario y es la propuesta #1 del plan (enfoque tipo juego).

## Propuesta E — Linea de metro / tren de la carrera

Un tren recorre una linea; cada estacion = un rol/ano. Los tramos (colores
distintos, estilo mapa de metro) = etapas de seniority (junior/mid/senior/lead).
Bajas en cada estacion a ver los proyectos.

- **Mapeo**: ano = estacion en orden, seniority = tramo/color de la linea +
  profundidad/altura de la estacion; pais del cliente = guiño (icono).
- **Pros**: la metafora "linea temporal" es literal y auto-explicativa; el
  **mapa de metro 2D es el fallback movil PERFECTO** (es, de hecho, un diagrama);
  on-rails = cero física.
- **Contras**: on-rails puede sentirse pasivo; el POV first-person es debil
  (vas sentado).
- **Esfuerzo**: **bajo.** Riesgo bajo. La mas barata de las on-rails.

## Propuesta F — Ciudad que crece

Empiezas en un descampado (2013) y al avanzar por la avenida la ciudad se
densifica: casas bajas -> edificios medios -> rascacielos (2026). Cada edificio
= un empleo/proyecto; la altura = seniority.

- **Mapeo**: ano = posicion en la avenida, seniority = altura del edificio;
  pais del cliente = guiño (un cartel), no distrito.
- **Pros**: la metafora "construir una carrera" es potente; altura = seniority
  es intuitiva y encaja de lleno con el eje; instancing de edificios low-poly
  es barato.
- **Contras**: riesgo de sentirse generico si los edificios se repiten; menos
  intimo que las salas de G.
- **Esfuerzo**: medio-alto. Riesgo medio.

## Resumen de eleccion

| Si quieres... | Elige |
|---------------|-------|
| **Experiencia tipo JUEGO: caminar sala a sala por puertas (#1)** | **A (habitaciones)** |
| Menor riesgo, posible CV principal (#2) | **B (scroll journey)** |
| Maximo wow / mundo abierto, aceptas 2-4 meses | **G (POV mundo libre)** |
| First-person real con el menor riesgo tecnico | **D (museo de salas)** |
| Lo mas barato con fallback perfecto | **E (metro/tren)** |
| La metafora "construir una carrera" (altura=seniority) | **F (ciudad que crece)** |
| Alcance remoto LATAM (secundaria, geografica) | **C (globo/mapa mercados)** |

> **A ([01-propuesta-a-habitaciones.md](01-propuesta-a-habitaciones.md))** es la
> #1 que pidio el usuario: POV inmersivo, una habitacion por experiencia
> ambientada por epoca/logro, conectadas por puertas con ida y vuelta,
> navegacion teclado/touch. Es la recomendada para el enfoque "tipo juego".

Todas comparten la [arquitectura comun](04-arquitectura-comun.md): misma app
`apps/journey`, mismos datos de `@portfolio/content`, mismo sistema de tiers/
fallback. Cambiar de propuesta = cambiar la escena, no la infraestructura.
