# 03 — Salas (indice)

> [<- 02 El canon](02-el-canon-de-sala.md) · [Descomposicion ->](04-descomposicion.md)

Las 8 salas del recorrido. La **Aula** (Etapa 1) se documenta aqui; las **7
salas de Etapa 2** tienen cada una su informe AUTOCONTENIDO (research completa:
experiencia, empresa, web oficial, guiños, NPCs con 2 enfoques, dialogos,
items, pasado, showcase, colores) para poder crearse en sesiones aisladas.

| Orden | Sala | Etapa | Informe | Estado |
| --- | --- | --- | --- | --- |
| 0 | `aula` | 1 | (aqui, abajo) | ver [ESTADO.md](ESTADO.md) |
| 1 | `corpoelec` | 2 | [08-sala-corpoelec.md](08-sala-corpoelec.md) | ver [ESTADO.md](ESTADO.md) |
| 2 | `ipasme` | 2 | [09-sala-ipasme.md](09-sala-ipasme.md) | ver [ESTADO.md](ESTADO.md) |
| 3 | `cofasa` | 2 | [10-sala-cofasa.md](10-sala-cofasa.md) | ver [ESTADO.md](ESTADO.md) |
| 4 | `dibal` | 2 | [11-sala-dibal.md](11-sala-dibal.md) | ver [ESTADO.md](ESTADO.md) |
| 5 | `goodmeal` | 2 | [12-sala-goodmeal.md](12-sala-goodmeal.md) | ver [ESTADO.md](ESTADO.md) |
| 6 | `destacame` | 2 | [13-sala-destacame.md](13-sala-destacame.md) | ver [ESTADO.md](ESTADO.md) |
| 7 | `futuro` | 2 | [14-sala-futuro.md](14-sala-futuro.md) | ver [ESTADO.md](ESTADO.md) |

Todas cumplen el canon de [02-el-canon-de-sala.md](02-el-canon-de-sala.md)
(office layout + NPCs 2 enfoques + wallArt + softwareShowcase + infoKit +
paredes blancas), salvo excepciones documentadas (aula sin showcase; futuro
sin pasado ni slug).

---

## Sala 0 — Aula (`aula`) · Etapa 1 · refactor MINIMO

Slug(s): `iai`, `projects-degrees` (proyecto academico IAI + asesoria de
proyectos de grado, 2015). Universidad. Acento azul `#2f6fd0` + guiños morados.

**Presente** (AC-9): MANTENER lo actual (2 tesistas sentados tecleando +
estudiante en ronda + PCs togglables con E + tesis en papel sobre el escritorio
del profesor). AGREGAR para llegar a 4-5 NPCs con los 2 enfoques:

- `[C]` compañero de proyecto de grado (tesista con el que Pablo saco adelante
  el proyecto que 2 equipos no lograron en meses).
- `[P]` compañero de universidad al que Pablo ayudo (cuenta como lo desatasco /
  lo capacito — de los ~6 estudiantes que capacito).
- `[J]` **profesor sentado en el escritorio del profesor** que habla bien de
  Pablo como ingeniero de software (su liderazgo temprano, la arquitectura
  cliente-servidor, el rescate de 1 semana).
- **wallArt**: diagramas cliente-servidor + el plan de rescate de 1 semana
  (1 inspeccionable = ficha del proyecto academico / la red local).
- **SIN softwareShowcase** (sala academica, no hay producto/sistema
  entregable). Es la unica sala presente sin showcase.

**Pasado**: **NO TOCAR** (decision del usuario: esta perfecto — Pablo pre-uni,
karate/videojuegos/A-C, cero codigo). En Etapa 1 se MUEVE tal cual a
`rooms/past/aula.ts` sin cambios de contenido (parte del refactor de partir
los pasados, commit C5).

**Retos/aprendizajes** (data-driven de `iai` + `projects-degrees`): reencaminar
2 proyectos de grado bloqueados; liderar un equipo pequeño; arquitectura de un
sistema de gestion de obras sobre red local. Aprendizajes: los reencamino en ~1
semana; capacito ~6 estudiantes; diseño cliente-servidor; documentacion +
diagnostico.

> Aula es la sala CANON (el infoKit, los NPCs conversables y los PCs togglables
> ya existen y son el modelo que replican las demas). Su refactor solo AGREGA
> NPCs + wallArt; no reescribe la escena.

---

## Salas 1-7 — Etapa 2

Ver el informe autocontenido de cada una (tabla arriba). Cada informe tiene la
misma estructura: checklist · datos reales (es/en) · rubro y ambiente · props
firma · cuadros de pared (`wallArt`) · softwareShowcase (demos) · NPCs (2
enfoques) · pasado (sepia) · retos y aprendizajes · fuentes.

Resumen de una linea por sala (el detalle esta en su informe):

- **corpoelec** — central electrica, inventario offline. Seccion de inventario
  con equipos (walkie/telefonos/PCs/tablets) + cascos + showcase gestion/
  buscador/reportes. Pasado: oficinas viejas, equipos regados, planillas x3
  sedes.
- **ipasme** — salud, historias clinicas (Java escritorio). Consultorio +
  showcase app de escritorio 2014. Pasado: archivo de carpetas manila +
  tarjetones + busqueda lenta.
- **cofasa** — laboratorio farma, paradas de maquina. Linea de blisters +
  MIOVIT (producto, no maquina) + torre andon + showcase dashboard de paradas.
  Pasado: planillas de paradas a mano.
- **dibal** — SaaS POS restaurantes (Peru). Salon + cocina, POS/KDS/impresora
  termica/SUNAT. Variante: Pablo unico dev -> dueño como stakeholder. Pasado:
  comandas en papelitos perdidos, boletas a mano.
- **goodmeal** — food-tech anti-desperdicio (Chile). Good Bags kraft + app +
  migracion Vue 3. Pasado: comida al tacho al cierre.
- **destacame** — fintech UNIFICADA (Chile+Mexico). 2 areas: PagaloAqui
  (Santander/Santander Consumer/Scotiabank) + producto Destacame (destacame.cl/
  .com.mx). Guiños intrinsecos: DS/DDD/microservicios/vibe/liderazgo. SIN
  Chile/Mexico en la entrada. Pasado: gente triste con deudas.
- **futuro** — SINTETICA (sin slug). Vision profesional + puerta Proximamente +
  CTA fuerte. Sin pasado, 0-1 NPC.
