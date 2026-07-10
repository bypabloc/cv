/**
 * @module rooms/past/asesoria (engine)
 * @description El "antes" de Asesoria/PROSALUD al nivel del canon
 *   (informe 17): los DOS hilos del caos en el mismo pasado sepia. Zona
 *   INSTITUTO sin sistema: sala de espera desbordada (sillas llenas de
 *   siluetas fusionadas), el pincho de papelitos de turno numerados a
 *   mano, el cuaderno de farmacia con tachones sobre un estante a medio
 *   inventariar, el archivador de afiliados con carpetas manila y el
 *   reloj de pared que cobra la mañana. Zona TESIS bloqueada: la mesa de
 *   los tesistas con el stack trace en pantalla (rojo sobre sepia), la
 *   pila de impresiones fallidas con tazas de cafe, la pizarra SIN plan
 *   (garabatos tachados + DEFENSA: 15 DIC rodeada en rojo) y el
 *   calendario con los meses tachados. Objeto de busqueda lenta: atender
 *   a un afiliado sin el sistema (buscar su carpeta Y su papelito — el
 *   papelito no aparece). 3 NPCs frustrados conversables: Jhonny junto
 *   al error, Coromoto con el cuaderno y Maigualida con los papelitos —
 *   los tres reaparecen en el presente usando el sistema.
 */
import { Group, Mesh, MeshBasicMaterial, PlaneGeometry } from 'three'
import type { Box2 } from '../../../lib/collision'
import type { Locale } from '../../../lib/rooms'
import { sfx } from '../../audio'
import { makeNpc, type NpcHandle } from '../../character'
import { npcTalk } from '../../dialog'
import { ASESORIA_PASADO_DIALOGS } from '../../dialogs/asesoria-pasado'
import type { Interactable } from '../../state'
import {
  boxMesh,
  label,
  makeCanvasTexture,
  mergedBoxes,
  outlinedMergedBoxes,
  screenPanel,
  toonMat,
} from '../../toon'
import type { PastCtx } from '../../world'
import { footprint, paperStack } from '../props'
import { placeProp } from '../props-catalog'
import { PAST_SCREEN, PAST_STORY_LABEL, type PastSet } from './shared'

const ASESORIA_STORY: Record<Locale, { title: string; paragraphs: string[] }> =
  {
    es: {
      title: 'Antes del rescate (2015)',
      paragraphs: [
        'En PROSALUD todo era papel: papelitos de turno numerados a ' +
          'mano que se perdian y se peleaban, un cuaderno de farmacia ' +
          'con mas tachones que letras y un archivador de carpetas ' +
          'manila donde buscar un afiliado era hojear y rezar. La cola ' +
          'de la mañana no bajaba nunca.',
        'A pocos metros, la otra crisis: la tesis que debia digitalizar ' +
          'ese caos llevaba MESES bloqueada. Codigo heredado que no ' +
          'compilaba, tres planes tachados en la pizarra y la fecha de ' +
          'defensa — 15 de diciembre — rodeada en rojo.',
        'En noviembre la directora corto el nudo: contrato a un ' +
          'muchacho que ya habia entregado dos sistemas en Yaracuy. Le ' +
          'pago por desarrollar la solucion EL SOLO y por enseñar al ' +
          'equipo a defenderla. Cruza de vuelta y ve como termino.',
      ],
    },
    en: {
      title: 'Before the rescue (2015)',
      paragraphs: [
        'At PROSALUD everything was paper: hand-numbered queue slips ' +
          'that got lost and fought over, a pharmacy notebook with more ' +
          'scribbles than words and a cabinet of manila folders where ' +
          'finding a member meant leafing and praying. The morning ' +
          'queue never shrank.',
        'A few metres away, the other crisis: the thesis meant to ' +
          'digitise that chaos had been stuck for MONTHS. Inherited ' +
          'code that would not compile, three crossed-out plans on the ' +
          'whiteboard and the defence date — December 15 — circled in ' +
          'red.',
        'In November the director cut the knot: she hired a young man ' +
          'who had already delivered two systems in Yaracuy. She paid ' +
          'him to build the solution ALONE and to teach the team to ' +
          'defend it. Cross back and see how it ended.',
      ],
    },
  }

const ATENDER_LABEL = {
  es: 'Atender a un afiliado sin el sistema',
  en: 'Serve a member without the system',
} as const

/** Cara del reloj de pared: esfera sepia con marcas horarias. */
function drawClockFace(ctx: CanvasRenderingContext2D, size: number): void {
  const c = size / 2
  ctx.fillStyle = '#e8d8b0'
  ctx.beginPath()
  ctx.arc(c, c, c - 8, 0, Math.PI * 2)
  ctx.fill()
  ctx.strokeStyle = '#201a10'
  ctx.lineWidth = 6
  ctx.stroke()
  for (let i = 0; i < 12; i += 1) {
    const angle = (i / 12) * Math.PI * 2
    const r0 = c - 16
    const r1 = i % 3 === 0 ? c - 34 : c - 24
    ctx.beginPath()
    ctx.moveTo(c + Math.cos(angle) * r0, c + Math.sin(angle) * r0)
    ctx.lineTo(c + Math.cos(angle) * r1, c + Math.sin(angle) * r1)
    ctx.lineWidth = i % 3 === 0 ? 5 : 3
    ctx.stroke()
  }
}

/** Pizarra SIN plan: garabatos tachados + DEFENSA: 15 DIC en rojo. */
function drawPizarraSinPlan(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#2c2620'
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = '#b09a6e'
  ctx.lineWidth = 3
  ctx.globalAlpha = 0.5
  ctx.strokeRect(8, 8, size - 16, size - 16)
  ctx.globalAlpha = 1
  ctx.lineCap = 'round'
  // tres "planes" garabateados y tachados
  const scraps = [
    ['plan A: arreglar lo roto', 44],
    ['plan B: empezar de cero', 92],
    ['plan C: ???', 140],
  ] as const
  ctx.font = '17px "Space Mono", ui-monospace, monospace'
  for (const [text, y] of scraps) {
    ctx.fillStyle = '#c8b48a'
    ctx.globalAlpha = 0.8
    ctx.fillText(text, 24, y)
    ctx.strokeStyle = '#c8b48a'
    ctx.lineWidth = 3
    ctx.beginPath()
    ctx.moveTo(20, y - 6)
    ctx.lineTo(24 + text.length * 9.4, y - 4)
    ctx.stroke()
  }
  ctx.globalAlpha = 1
  // la fecha de defensa rodeada en rojo, la unica certeza
  ctx.fillStyle = '#c26a5a'
  ctx.font = 'bold 24px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('DEFENSA: 15 DIC', 34, 205)
  ctx.strokeStyle = '#c26a5a'
  ctx.lineWidth = 4
  ctx.beginPath()
  ctx.ellipse(122, 197, 104, 26, -0.03, 0, Math.PI * 2)
  ctx.stroke()
}

/** Calendario con los meses tachados: el tiempo que se perdio. */
function drawCalendario(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#e8dcc0'
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = '#201a10'
  ctx.lineWidth = 4
  ctx.strokeRect(6, 6, size - 12, size - 12)
  ctx.fillStyle = '#201a10'
  ctx.font = 'bold 20px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('2015', 100, 36)
  const months = [
    ['AGO', true],
    ['SEP', true],
    ['OCT', true],
    ['NOV', false],
  ] as const
  ctx.lineCap = 'round'
  months.forEach(([name, crossed], index) => {
    const col = index % 2
    const row = Math.floor(index / 2)
    const x = 28 + col * 110
    const y = 58 + row * 90
    ctx.strokeStyle = '#201a10'
    ctx.lineWidth = 2
    ctx.strokeRect(x, y, 92, 68)
    ctx.fillStyle = '#201a10'
    ctx.font = 'bold 16px "Space Mono", ui-monospace, monospace'
    ctx.fillText(name, x + 8, y + 22)
    // mini-grilla de dias
    ctx.globalAlpha = 0.4
    for (let d = 0; d < 3; d += 1) {
      ctx.beginPath()
      ctx.moveTo(x + 8, y + 34 + d * 10)
      ctx.lineTo(x + 84, y + 34 + d * 10)
      ctx.stroke()
    }
    ctx.globalAlpha = 1
    if (crossed) {
      ctx.strokeStyle = '#8a4a3a'
      ctx.lineWidth = 5
      ctx.beginPath()
      ctx.moveTo(x + 6, y + 6)
      ctx.lineTo(x + 86, y + 62)
      ctx.moveTo(x + 86, y + 6)
      ctx.lineTo(x + 6, y + 62)
      ctx.stroke()
    }
  })
  ctx.fillStyle = '#8a4a3a'
  ctx.font = 'bold 12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('el tiempo se fue', 66, 246)
}

/** El "antes" de PROSALUD: instituto en papel + mesa de tesis varada. */
export function asesoriaPast(
  x: number,
  z: number,
  depth: number,
  locale: Locale,
  actions: PastCtx['actions'],
): PastSet {
  const group = new Group()
  const colliders: Box2[] = []
  const npcs: NpcHandle[] = []
  const interactables: Interactable[] = []
  const updates: ((t: number, dt: number) => void)[] = []

  // ZONA INSTITUTO (frente): sala de espera desbordada — dos hileras de
  // sillas con siluetas sentadas (lotes fusionados)
  const chairRows: readonly (readonly [number, number])[] = [
    [x - 3.6, z + 1.4],
    [x - 3.6, z + 2.6],
  ]
  group.add(
    outlinedMergedBoxes(
      chairRows.flatMap(([cx, cz]) =>
        [-0.9, 0, 0.9].flatMap((dx) => [
          { w: 0.5, h: 0.06, d: 0.45, x: cx + dx, y: 0.46, z: cz },
          { w: 0.5, h: 0.45, d: 0.06, x: cx + dx, y: 0.74, z: cz + 0.22 },
          {
            w: 0.05,
            h: 0.44,
            d: 0.05,
            x: cx + dx - 0.2,
            y: 0.22,
            z: cz + 0.1,
          },
          {
            w: 0.05,
            h: 0.44,
            d: 0.05,
            x: cx + dx + 0.2,
            y: 0.22,
            z: cz + 0.1,
          },
        ]),
      ),
      toonMat('#5a5244'),
      { inflate: 0.03, castShadow: true },
    ),
    // la sala LLENA: siluetas sentadas en casi todas las sillas
    outlinedMergedBoxes(
      chairRows.flatMap(([cx, cz], row) =>
        [-0.9, 0, 0.9]
          .filter((_, i) => !(row === 1 && i === 1))
          .flatMap((dx) => [
            {
              w: 0.38,
              h: 0.52,
              d: 0.3,
              x: cx + dx,
              y: 0.78,
              z: cz + 0.06,
            },
            {
              w: 0.24,
              h: 0.24,
              d: 0.24,
              x: cx + dx,
              y: 1.18,
              z: cz + 0.06,
            },
          ]),
      ),
      toonMat('#4c4438'),
      { castShadow: true },
    ),
  )
  colliders.push(
    footprint(x - 3.6, z + 1.4, 2.6, 0.6),
    footprint(x - 3.6, z + 2.6, 2.6, 0.6),
  )

  // mostrador de admision saturado GLB: el pincho de papelitos + planillas
  group.add(
    placeProp('reception_counter', {
      x: x + 0.6,
      z: z + 2.0,
      width: 1.5,
      color: '#4c4740',
    }),
  )
  colliders.push(footprint(x + 0.6, z + 2.0, 1.6, 0.8))
  group.add(
    // pincho: base + aguja + papelitos ensartados
    mergedBoxes(
      [
        { w: 0.12, h: 0.02, d: 0.12, x: x + 0.25, y: 0.755, z: z + 1.9 },
        { w: 0.015, h: 0.22, d: 0.015, x: x + 0.25, y: 0.87, z: z + 1.9 },
        { w: 0.09, h: 0.008, d: 0.07, x: x + 0.25, y: 0.86, z: z + 1.9 },
        {
          w: 0.09,
          h: 0.008,
          d: 0.07,
          x: x + 0.26,
          y: 0.83,
          z: z + 1.91,
          rotY: 0.5,
        },
        {
          w: 0.09,
          h: 0.008,
          d: 0.07,
          x: x + 0.24,
          y: 0.8,
          z: z + 1.89,
          rotY: -0.4,
        },
      ],
      toonMat('#e8d8b0'),
    ),
  )
  group.add(
    paperStack({ position: [x + 1.05, 0.745, z + 2.1], count: 9 }),
    paperStack({ position: [x + 0.6, 0.745, z + 2.25], count: 5 }),
  )
  const turnosSign = label(
    locale === 'es' ? 'TURNOS: a mano' : 'TICKETS: by hand',
    { size: 0.12, color: '#e8d8b0' },
  )
  turnosSign.position.set(x + 0.6, 1.3, z + 2.0)
  group.add(turnosSign)

  // farmacia a medio inventariar (+X): estante con cajas sin orden + el
  // cuaderno de tachones abierto sobre una mesita
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.5, h: 0.04, d: 1.6, x: x + 3.6, y: 0.6, z: z - 0.6 },
        { w: 0.5, h: 0.04, d: 1.6, x: x + 3.6, y: 1.2, z: z - 0.6 },
        { w: 0.5, h: 1.3, d: 0.05, x: x + 3.6, y: 0.65, z: z - 1.42 },
        { w: 0.5, h: 1.3, d: 0.05, x: x + 3.6, y: 0.65, z: z + 0.22 },
      ],
      toonMat('#5a5750'),
      { castShadow: true },
    ),
    // cajas apiladas sin orden (algunas de canto, una en el piso)
    mergedBoxes(
      [
        { w: 0.2, h: 0.12, d: 0.26, x: x + 3.6, y: 0.68, z: z - 1.1 },
        {
          w: 0.16,
          h: 0.22,
          d: 0.1,
          x: x + 3.6,
          y: 0.73,
          z: z - 0.7,
          rotY: 0.4,
        },
        { w: 0.2, h: 0.12, d: 0.24, x: x + 3.62, y: 0.82, z: z - 1.08 },
        {
          w: 0.18,
          h: 0.1,
          d: 0.22,
          x: x + 3.6,
          y: 1.27,
          z: z - 0.3,
          rotY: -0.3,
        },
        { w: 0.2, h: 0.12, d: 0.26, x: x + 3.2, y: 0.06, z: z + 0.5 },
      ],
      toonMat('#b09a6e'),
    ),
  )
  colliders.push(footprint(x + 3.6, z - 0.6, 0.7, 1.8))
  group.add(
    placeProp('desk_office', {
      x: x + 2.6,
      z: z + 0.9,
      rotationY: -Math.PI / 2,
      width: 0.9,
      color: '#4c4740',
    }),
  )
  colliders.push(footprint(x + 2.6, z + 0.9, 0.7, 1.0))
  // el cuaderno abierto (dos paginas) con lineas de tachones
  group.add(
    mergedBoxes(
      [
        {
          w: 0.24,
          h: 0.015,
          d: 0.32,
          x: x + 2.47,
          y: 0.745,
          z: z + 0.9,
          rotY: 0.06,
        },
        {
          w: 0.24,
          h: 0.015,
          d: 0.32,
          x: x + 2.73,
          y: 0.745,
          z: z + 0.9,
          rotY: -0.06,
        },
      ],
      toonMat('#e8dcc0'),
    ),
  )
  const cuadernoSign = label(
    locale === 'es' ? 'inventario: tachones' : 'inventory: scribbles',
    { size: 0.11, color: '#e8d8b0' },
  )
  cuadernoSign.position.set(x + 2.6, 1.25, z + 0.9)
  group.add(cuadernoSign)

  // archivador de afiliados: gabinete + cajon abierto con carpetas
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.6, h: 1.4, d: 0.5, x: x + 3.55, y: 0.7, z: z + 2.2 },
        { w: 0.5, h: 0.24, d: 0.44, x: x + 3.55, y: 1.16, z: z + 2.48 },
      ],
      toonMat('#5a5750'),
      { castShadow: true },
    ),
  )
  // carpetas del cajon en coords LOCALES (el pivote es el gabinete):
  // asi el temblor de la busqueda rota alrededor del archivador
  const carpetas = mergedBoxes(
    [
      { w: 0.3, h: 0.16, d: 0.03, x: -0.08, y: 1.36, z: 0.3 },
      { w: 0.3, h: 0.14, d: 0.03, x: 0, y: 1.35, z: 0.35 },
      { w: 0.3, h: 0.15, d: 0.03, x: 0.08, y: 1.355, z: 0.25 },
    ],
    toonMat('#b09a6e'),
  )
  carpetas.position.set(x + 3.55, 0, z + 2.2)
  group.add(carpetas)
  colliders.push(footprint(x + 3.55, z + 2.2, 0.7, 0.8))

  // reloj de pared: la mañana que se va en la cola
  const clock = new Group()
  clock.position.set(x - 1.2, 2.5, z - depth / 2 + 0.1)
  const faceMesh = new Mesh(
    new PlaneGeometry(0.72, 0.72),
    new MeshBasicMaterial({ map: makeCanvasTexture(128, drawClockFace) }),
  )
  faceMesh.userData.noOutline = true
  const hand = boxMesh(0.04, 0.26, 0.02, toonMat('#201a10'))
  hand.position.z = 0.02
  hand.userData.noOutline = true
  clock.add(faceMesh, hand)
  group.add(clock)
  updates.push((t) => {
    // la aguja da una vuelta cada ~12 s: la mañana que se pierde
    hand.rotation.z = -t * 0.52
  })

  // ZONA TESIS (fondo): la mesa GLB de los tesistas con el stack trace, la
  // pila de intentos fallidos y las tazas de cafe
  group.add(
    placeProp('desk_office', {
      x: x - 2.6,
      z: z - 1.6,
      width: 1.6,
      color: '#4c4740',
    }),
  )
  colliders.push(footprint(x - 2.6, z - 1.6, 1.7, 0.8))
  // laptop 2015 con el error fatal en pantalla (rojo sobre sepia)
  const errorPanel = screenPanel({
    title: 'error.log',
    lines: [
      'Fatal error: Call to',
      ' undefined function',
      ' consultar_turnos()',
      'in citas.php line 84',
      '',
      'build: FAILED (otra vez)',
    ],
    theme: { ...PAST_SCREEN, screenFg: '#c26a5a' },
    width: 0.72,
    height: 0.5,
  })
  errorPanel.position.set(x - 2.6, 1.05, z - 1.75)
  errorPanel.rotation.y = Math.PI
  group.add(errorPanel)
  group.add(
    // base de la laptop bajo el panel
    mergedBoxes(
      [{ w: 0.66, h: 0.03, d: 0.42, x: x - 2.6, y: 0.76, z: z - 1.6 }],
      toonMat('#3a352c'),
    ),
    // tazas de cafe de la trasnochada
    mergedBoxes(
      [
        { w: 0.09, h: 0.11, d: 0.09, x: x - 3.25, y: 0.8, z: z - 1.45 },
        { w: 0.09, h: 0.11, d: 0.09, x: x - 1.95, y: 0.8, z: z - 1.8 },
        { w: 0.09, h: 0.11, d: 0.09, x: x - 2.1, y: 0.8, z: z - 1.42 },
      ],
      toonMat('#8a7a5e'),
    ),
  )
  group.add(
    paperStack({ position: [x - 1.7, 0, z - 1.2], count: 14 }),
    paperStack({ position: [x - 3.4, 0, z - 2.0], count: 8 }),
  )

  // pizarra sin plan + calendario tachado en el muro del fondo
  const pizarra = new Mesh(
    new PlaneGeometry(1.6, 1.15),
    new MeshBasicMaterial({ map: makeCanvasTexture(256, drawPizarraSinPlan) }),
  )
  pizarra.userData.noOutline = true
  pizarra.position.set(x - 2.6, 1.85, z - depth / 2 + 0.1)
  group.add(pizarra)
  const calendario = new Mesh(
    new PlaneGeometry(0.85, 0.85),
    new MeshBasicMaterial({ map: makeCanvasTexture(256, drawCalendario) }),
  )
  calendario.userData.noOutline = true
  calendario.position.set(x - 0.2, 1.85, z - depth / 2 + 0.1)
  group.add(calendario)

  // micro: atender a un afiliado sin el sistema — el archivador tiembla,
  // la carpeta aparece tarde... y el papelito del turno no aparece
  const verdict1 = label(
    locale === 'es'
      ? '9 min: la carpeta aparecio...'
      : '9 min: the folder showed up...',
    { size: 0.13, color: '#e8d8b0' },
  )
  verdict1.position.set(x + 3.4, 2.35, z + 2.2)
  verdict1.visible = false
  group.add(verdict1)
  const verdict2 = label(
    locale === 'es'
      ? '...¿y su papelito? PERDIDO. Turno de nuevo'
      : '...and their slip? LOST. Queue again',
    { size: 0.13, color: '#c8a878' },
  )
  verdict2.position.set(x + 3.0, 2.05, z + 2.2)
  verdict2.visible = false
  group.add(verdict2)
  let searchT = -1
  interactables.push({
    id: 'past-search',
    x: x + 3.55,
    z: z + 2.2,
    radius: 2.2,
    label: ATENDER_LABEL,
    onActivate: () => {
      if (searchT === -1) {
        searchT = -2 // pendiente: el proximo update fija el inicio
        sfx.play('blip')
      }
    },
  })
  updates.push((t) => {
    if (searchT === -2) {
      searchT = t
    }
    if (searchT < 0) {
      return
    }
    const elapsed = t - searchT
    if (elapsed < 2.2) {
      // hojear el archivador: las carpetas del cajon tiemblan
      verdict1.visible = false
      verdict2.visible = false
      carpetas.rotation.y = Math.sin(t * 22) * 0.05
    } else if (elapsed < 4.4) {
      carpetas.rotation.y = 0
      verdict1.visible = true
    } else if (elapsed < 7.2) {
      verdict2.visible = true
    } else {
      verdict1.visible = false
      verdict2.visible = false
      searchT = -1
    }
  })

  // Jhonny (antes) de pie junto al stack trace que no cede — el mismo
  // tesista que en el presente explica el sistema linea por linea
  const jhonny = makeNpc({
    skin: '#c98f6a',
    hair: { style: 'short', color: '#14100c' },
    top: '#6a6152',
    bottom: '#4a4438',
    accessory: 'glasses',
    model: 'brian',
    faceSeed: 41,
    position: [x - 2.6, 0, z - 0.9],
    rotationY: Math.PI,
    // crisis del rubro (pedido de Pablo): la frustracion por sobrecarga
    pose: 'frustrated',
  })
  // Coromoto (antes) con su cuaderno de tachones en la farmacia a medio
  // inventariar
  const coromoto = makeNpc({
    skin: '#d9a684',
    hair: { style: 'bun', color: '#5a4a3a' },
    top: '#8a8270',
    bottom: '#5a5548',
    accessory: 'badge',
    model: 'chad',
    faceSeed: 53,
    position: [x + 2.6, 0, z + 0.25],
    rotationY: Math.PI,
    // crisis del rubro (pedido de Pablo): el estres de la sobrecarga de trabajo
    pose: 'yelling',
  })
  // Maigualida (antes) entre el pincho y la cola, repartiendo papelitos
  const maigualida = makeNpc({
    skin: '#b5825f',
    hair: { style: 'bun', color: '#1c1410' },
    top: '#7a6a58',
    bottom: '#4a4438',
    model: 'kate',
    faceSeed: 34,
    position: [x + 0.3, 0, z + 1.3],
    path: [
      [x + 0.3, z + 1.3],
      [x - 2.0, z + 1.9],
      [x + 0.9, z + 2.5],
    ],
    speed: 0.5,
  })
  npcs.push(jhonny, coromoto, maigualida)
  const talks = [
    npcTalk({
      id: 'talk-past-asesoria-jhonny',
      npc: jhonny,
      dialog: ASESORIA_PASADO_DIALOGS.jhonny,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-asesoria-coromoto',
      npc: coromoto,
      dialog: ASESORIA_PASADO_DIALOGS.coromoto,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-asesoria-maigualida',
      npc: maigualida,
      dialog: ASESORIA_PASADO_DIALOGS.maigualida,
      openDialog: actions.openDialog,
    }),
  ]
  for (const talk of talks) {
    interactables.push(talk.interactable)
    updates.push(talk.update)
  }

  const story = ASESORIA_STORY[locale]
  const panel = screenPanel({
    title: locale === 'es' ? 'dos crisis a la vez' : 'two crises at once',
    lines:
      locale === 'es'
        ? [
            'instituto: puro papel',
            'tesis: 4 meses varada',
            'defensa: 15 DIC',
            'contrato: noviembre',
            '',
            '[E] leer la historia',
          ]
        : [
            'institute: all paper',
            'thesis: stuck 4 months',
            'defence: DEC 15',
            'contract: November',
            '',
            '[E] read the story',
          ],
    theme: PAST_SCREEN,
    width: 1.8,
    height: 1.25,
  })
  panel.position.set(x + 1.6, 1.6, z - depth / 2 + 0.12)
  group.add(panel)
  interactables.push({
    id: 'past-story',
    x: x + 1.6,
    z: z - depth / 2 + 0.5,
    radius: 2.4,
    label: PAST_STORY_LABEL,
    onActivate: () => actions.openStory(story.title, story.paragraphs),
  })
  return { group, colliders, npcs, interactables, updates }
}
