# Propuesta B — Scroll-driven journey (#2 / alternativa de menor riesgo)

> [<- Propuesta A (habitaciones)](01-propuesta-a-habitaciones.md) · [Siguiente: extras ->](03-propuestas-extra.md)

Scrolleas y la camara viaja por un **sendero 3D fijo** que atraviesa tu
crecimiento profesional como estaciones: intern -> junior -> mid -> senior ->
lead/arquitecto. Cada rol/proyecto es un hito. El mundo se vuelve mas complejo
y elevado a medida que subes de nivel. Es el patron premiado 2025-2026
(Awwwards/FWA), el de menor riesgo.

## Eje protagonista: PROGRESION PROFESIONAL (no geografia)

El viaje estructura tu **ascenso de seniority + complejidad tecnica**, NO un
arco migratorio. Correccion del usuario (2026-07-02): reside en Lima, Peru;
trabaja remoto para clientes de Chile/Mexico; el `country` de los datos es el
del cliente, NO residencia. La geografia es un GUINO SUTIL, nunca la columna.

### Las estaciones = niveles de carrera

- **Intern / Junior (2013-2014)** — el punto de partida. Escena minima,
  a ras de suelo: primeros sistemas web. Herramienta simple, mundo pequeño.
- **Mid + primer liderazgo (2015-2018)** — el terreno se eleva un poco;
  aparecen los primeros hitos de "lider de desarrollo y arquitectura".
- **Senior (2018-2021)** — salto notorio de elevacion y detalle: lideras
  equipo, ERP, sistemas mas grandes. El mundo se vuelve mas rico.
- **Lead / Arquitecto (2022-hoy)** — la cima: microservicios, arquitectura
  frontend, fintech, AWS, AI workflows. Vista mas alta, mas compleja,
  panoramica. Aqui estas ahora.

Caminas hacia adelante = avanzas en el tiempo Y en seniority (los dos ejes
crecen juntos en tu carrera). Al llegar al presente, la camara se eleva a un
**overlook** del recorrido completo (12 anos, 8 empresas, stack completo).

## Mapeo a datos reales (SIN texto, eje = seniority)

| Eje del dato | Codificacion visual |
|--------------|---------------------|
| **Seniority (intern->lead)** | **ELEVACION + escala del mundo + complejidad de la escena** (eje protagonista) |
| Ano (2013-2026) | Distancia recorrida sobre el sendero (t del spline) |
| Complejidad tecnica | Densidad de props/estructuras: de 1 pieza simple (junior) a un skyline de sistemas interconectados (arquitecto) |
| Empresa / rol | Un hito al costado (monolito, estacion, plataforma) |
| Proyecto (ERP, fintech, microservicios) | Vitrina que abre la ficha HTML del proyecto |
| Pais del cliente (VE/PE/CL/MX) | **GUINO SUTIL**: etiqueta/banderita pequeña en la ficha del hito, NO estructura la escena |
| stats (12/8/4/11) | Overlook final: contadores animados |

Fuente: `@portfolio/content` (9 experiences + projects + skills). Cada hito es
data-driven: agregar un rol = agregar el YAML, el sendero se recalcula.

## Metafora visual (opciones para el eje seniority)

El sendero puede materializar "subir de nivel" de varias formas — a elegir en
art direction:

- **Ascenso de altura**: el sendero sube de un valle (intern) a una cima
  (arquitecto). Elevacion literal = seniority. La mas directa.
- **Mundo que se sofistica**: de un boceto/wireframe (junior) a un entorno
  detallado e iluminado (lead). La complejidad de render = madurez tecnica.
- **De pieza a sistema**: empiezas con 1 objeto (una funcion/pagina) y al
  avanzar los objetos se conectan en un sistema (microservicios, arquitectura).
  Refuerza tu identidad de arquitecto.

Guiño geografico: cada hito lleva una etiqueta discreta del cliente/pais, o un
pequeño detalle de skybox, sin que el pais organice el recorrido.

## Mecanica tecnica

- **Camino maestro**: `THREE.CatmullRomCurve3` con ~20-30 control points.
  Scroll normalizado 0..1 -> `curve.getPointAt(t)` para la camara; segundo
  spline (o `getPointAt(t + ε)`) para el `lookAt`.
- **Suavizado**: lerp/damping 0.05-0.1 (mata el jitter, feel cinematico).
- **Scroll**: Lenis + GSAP ScrollTrigger:

  ```js
  lenis.on('scroll', ScrollTrigger.update)
  gsap.ticker.add((time) => lenis.raf(time * 1000))
  ```

- **Micro-animaciones por estacion**: GSAP timelines pinneados (fade del texto
  del hito, aparicion de props, "subida de nivel" al cruzar a la siguiente
  etapa de seniority). ScrollTrigger `scrub: true`.
- **Texto del CV**: overlay HTML estatico (indexable), NUNCA dentro del WebGL.

## Estetica recomendada

**Low-poly / estilizado** (baratos, livianos, coherentes). Assets base de
Kenney + Quaternius. Baking de sombras + matcaps (sin luces dinamicas). La
progresion de complejidad visual (de simple a sofisticado) refuerza el eje
seniority sin costo extra de assets.

## Fallback movil (3 tiers)

- **Full** (desktop GPU): sendero 3D completo con la progresion de elevacion/
  complejidad + overlook final.
- **Reduced** (movil con WebGL): misma escena, menos polys, sin post-processing,
  DPR capado, camara guiada por scroll.
- **Static** (sin WebGL / HW debil / `prefers-reduced-motion`): el sendero se
  vuelve un **timeline 2D vertical** — secciones apiladas por etapa de carrera
  (intern -> lead) con el texto completo del CV. Este ES el storytelling
  legible que pediste y el fallback SEO/ATS.

## Referencias reales (del research)

- **Sébastien Lempens** (sebastien-lempens.com) — tour scroll-driven 3D.
- **Aimee's Papercraft** (aimees-papercraft-world.com) — OPEN SOURCE, estetica
  barata.
- **JReyes MC** (jreyes-mc-portfolio.com) — journey voxel, Awwwards HM.
- **Codrops nov-2025** — tutorial "cinematic 3D scroll con GSAP".
- **The Monolith Project** (themonolithproject.net) — 13 escenas scroll-driven
  que van de bocetos a mundos iluminados (encaja perfecto con "de junior a
  arquitecto").

Tabla completa + URLs en [../../progress/explore_scroll3d_journey.md](../../progress/explore_scroll3d_journey.md).

## Esfuerzo

- Andamiaje base (escena + camino + scroll sync): 16-40 h.
- Proyecto pulido: **2-3 semanas** si se domina R3F, **3-6 semanas** aprendiendo.
- Lo caro: assets 3D (mitigar low-poly) > calibrar spline / jitter > sync
  scroll<->texto > fallback/tiers > perf tuning.

## Por que es la #2 (alternativa fuerte a la A)

La #1 del plan es la Propuesta A (habitaciones, tipo juego) por decision del
usuario. Esta (B, scroll) es la alternativa recomendada cuando se prioriza
riesgo/indexabilidad:

- Mapea tu crecimiento profesional real (intern->arquitecto) — el mensaje que
  importa a un reclutador.
- **Menor riesgo tecnico de todas** (on-rails, sin physics) — mas segura que A.
- Degrada perfecto a un timeline 2D que ES el fallback SEO/ATS.
- **La mejor candidata a CV principal indexable** sin romper el ADN del
  portfolio. Puede convivir con A: B como `/` (scroll), A como `/world` (juego).
