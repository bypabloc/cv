# 14 — Sala Futuro (Etapa 2, sala 7) — SINTETICA

> Informe AUTOCONTENIDO para crear la sala `futuro` en una sesion aislada.
> Prerequisito: Etapa 1 hecha. Leer antes: [README](README.md) +
> [02-el-canon-de-sala.md](02-el-canon-de-sala.md) + [ESTADO.md](ESTADO.md).
>
> Sala **SINTETICA**: NO deriva de una experiencia del CV (no tiene slug).
> Es el cierre inspiracional del recorrido: la vision profesional de Pablo
> (hacia donde va) + la puerta "Proximamente" + el CTA de contacto FUERTE.
> Sus textos son literales (no data-driven de `@portfolio/content`).

## Checklist de la sala

- [ ] `engine/rooms/futuro.ts` (presente)
- [ ] `engine/dialogs/futuro-presente.ts` (SOLO si lleva 1 NPC, opcional)
- [ ] spec sintetico en `lib/rooms.ts` (textos LITERALES, no derivados de slug)
- [ ] theme `futuro` con `wall: '#f2f0eb'` (verificar)
- [ ] SIN `rooms/past/futuro.ts` (no hay "antes" de una vision)
- [ ] typecheck + build + visual OK
- [ ] Actualizar [ESTADO.md](ESTADO.md)

## 0. Excepciones documentadas al canon

Esta sala es de CIERRE, no una empresa. Rompe 3 reglas del canon a proposito:

- **AC-5 (4-5 NPCs)**: NO aplica. La sala lleva 0-1 NPC (opcional un "Pablo
  del futuro" aspiracional). No hay compañeros/personal del sitio (no es una
  empresa).
- **AC-20 (pasado)**: NO aplica. No hay portal al pasado (no existe un "antes"
  de una vision). El `infoKit` se usa **SIN la grieta al pasado** (o con un
  guiño distinto: una puerta a "lo que viene" en vez de a "lo que fue").
- **Data-driven**: NO aplica. `buildRooms` derivaria de un slug; `futuro` no
  tiene. Su spec en `lib/rooms.ts` lleva los textos LITERALES (retos/
  aprendizajes reemplazados por "metas"/"vision"). Ver §5.

El resto del canon SI aplica: paredes blancas, `wallArt`, CTA, kit (sin
grieta), 1 solo content de sala vivo, tiers.

## 1. Concepto y tono

**Vision profesional: hacia donde va Pablo.** Sala aspiracional, luminosa,
horizonte abierto. Representa las metas de la siguiente etapa de la carrera:

- **Staff / Principal Engineer** — el siguiente escalon tecnico.
- **Mas IA + arquitectura** — profundizar en AI workflows / vibe coding a
  escala + arquitectura de sistemas distribuidos.
- **Mentoria / liderazgo tecnico** — formar equipos, multiplicar impacto.

Es el climax emocional del recorrido: tras 6 salas de historia real, esta
mira adelante e invita al reclutador a la accion (contacto).

## 2. Ambiente (presente, sintetico)

- **Roadmap en pizarra** — una pizarra grande con la vision dibujada: hitos
  futuros como nodos en una linea de tiempo ascendente (staff -> principal;
  IA a escala; mentoria). Estilo tinta plana, manga-ink.
- **Horizonte luminoso** — la iluminacion de la sala es la mas clara/optimista
  del recorrido (amanecer/apertura), contrasta con el war-room premium de
  Destacame: aqui es luz de posibilidad, no de estatus.
- **Puerta "Proximamente"** grande y central (ideas futuras) — se puede
  **mover aqui** la que hoy vive en la CIMA/Destacame, o mantener ambas. Al
  fondo, insinua lo que viene, invita a volver.
- **CTA de contacto FUERTE** — el objeto focal (holograma / telefono /
  tarjeta) que abre el contacto + CV-PDF + LinkedIn (`actions.openContact()`).
  Reusar el holograma+pedestal de la CIMA actual (`rooms/cima.ts:476`).
  Es el objetivo de negocio del portfolio: convertir la experiencia en accion.
- **(Opcional) 1 NPC "Pablo del futuro"** aspiracional — si se pone, un solo
  NPC conversable que habla en primera persona de las metas. Si no, la sala
  funciona sin NPCs (es de cierre).

**Paleta**: pared `#f2f0eb` blanca (como todas); acento **azul-violeta neutro
premium** (`~#5a6ff0`) en piso/props/luz — un tono distinto del azul Destacame
(`#0052cc`) para que se sienta "adelante", no "mas Destacame". Trim
`~#a0a8d8`, lightColor `~#eef0ff` (el mas claro del recorrido).

## 3. Props firma (sinteticos)

- **Pizarra de roadmap** (nodos futuros en timeline ascendente).
- **Holograma/CTA de contacto** sobre pedestal (reusar de la CIMA).
- **Puerta "Proximamente"** (reusar de la CIMA, `rooms/cima.ts:444`).
- Escritorios con laptops (canon `officeLayout`, densidad baja) si se quiere
  ambientar; opcional dado que no es una empresa.

## 4. Cuadros de pared (`wallArt`)

2-3 laminas, **1 inspeccionable** (★):

1. **★ Manifiesto "hacia donde voy"** — un cuadro con la vision escrita (es/en):
   staff/principal, IA + arquitectura, mentoria. **INSPECCIONABLE** (abre la
   ficha con el manifiesto completo — es el corazon de la sala).
2. **Tecnologias del futuro** — lamina con los ejes tecnicos a profundizar
   (AI workflows, sistemas distribuidos, arquitectura). Decorativo.
3. (Opcional) **Un guiño al vibe coding / a como se construyo este journey**
   — puente a la meta-narrativa (Astro + Three.js + Claude Code). Decorativo.

## 5. Textos sinteticos (para `lib/rooms.ts`)

Como no hay slug, el spec de `futuro` lleva textos LITERALES. En vez de
retos/aprendizajes de una experiencia, usar **metas** (es/en):

**"Retos" (reinterpretado como PROXIMOS DESAFIOS)**
- es: "Crecer a Staff / Principal Engineer sin dejar de construir."
- es: "Llevar la IA (vibe coding, AI workflows) a la escala de un equipo."
- es: "Multiplicar impacto via mentoria y liderazgo tecnico."
- en: analogo.

**"Aprendizajes" (reinterpretado como LO QUE QUIERE APORTAR)**
- es: "Arquitectura de sistemas distribuidos robustos y observables."
- es: "Equipos que shippean con estandares y sin acoplamiento."
- es: "Adopcion de IA productiva y segura como norma del equipo."
- en: analogo.

**Reseña del cuaderno / represents**
- es: "Esta sala representa hacia donde voy: el siguiente escalon tecnico,
  la IA a escala y la mentoria. El recorrido termina mirando adelante —
  hablemos."
- en: "This room represents where I'm heading: the next technical step, AI at
  scale, and mentorship. The journey ends looking forward — let's talk."

## 6. Sin pasado (AC excepcion)

NO crear `rooms/past/futuro.ts`. El `infoKit` se invoca sin la grieta al
pasado (parametro/variante que omite el portal). Verificar que el motor no
asuma que toda sala tiene pasado (revisar `world.ts` enterPast + `PAST_CAPTIONS`
+ el shell del pasado — `futuro` no debe registrarse ahi, o registrarse como
"sin pasado"). Si el motor exige un pasado por sala, la salida minima es una
mini-escena vacia; preferible: soportar "sala sin grieta" en el canon.

> Nota de infra: esto puede requerir un pequeño ajuste en Etapa 1 (que el
> `infoKit`/world soporte una sala sin grieta). Si Etapa 1 no lo previo,
> documentarlo aqui y hacerlo al crear `futuro` (es la unica sala sin pasado).

## 7. Verificacion especifica

- Build OK **sin slug** (el spec sintetico no llama a `buildRooms` con un slug
  inexistente — usa textos literales).
- CTA de contacto abre el panel de contacto (`openContact`).
- Puerta "Proximamente" presente.
- Sin grieta al pasado (o grieta reinterpretada).
- Teleport (M) lista `futuro` como la sala 8/8.

## Fuentes

Sintetica — sin fuente de CV. Basada en: la decision del usuario ("vision
profesional"), el plan `journey-3d-cv/01-propuesta-a-habitaciones.md` (la
puerta "Proximamente" + CTA de la Sala 8/CIMA), y el CTA/holograma existente
en `engine/rooms/cima.ts` (a reusar).
