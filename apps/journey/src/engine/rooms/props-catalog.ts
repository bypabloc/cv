/**
 * @module rooms/props-catalog (engine)
 * @description Catalogo de props GLB CC0 del recorrido (73 modelos en
 *   public/models/furniture/, ver public/models/CREDITS.md +
 *   tmp/assets/catalogo_assets.csv). Mapea un `id` semantico (snake_case,
 *   la clave del catalogo) a su url + ancho objetivo por defecto (unidades
 *   de mundo). El helper `prop()` envuelve `placeFurniture` para que las
 *   salas coloquen un GLB por nombre: `prop('desk_office', { x, z })`.
 *   El GLB se convierte a `MeshToonMaterial` en runtime (mismo lenguaje que
 *   el resto de la sala); las pantallas siguen siendo Canvas (SEO/a11y).
 */
import type { Group } from 'three'
import { type FurnitureOpts, placeFurniture } from './furniture'

const DIR = '/models/furniture'

/** Entrada del catalogo: url del GLB + ancho objetivo por defecto (m). */
export interface PropEntry {
  url: string
  /** Ancho objetivo por defecto (auto-escala desde el bounding box). */
  w: number
}

/**
 * Los 73 props CC0 conseguidos, por id del catalogo. El `w` es el ancho
 * por defecto; una sala puede sobreescribirlo con `widthOverride`.
 */
export const PROPS = {
  ac_unit: { url: `${DIR}/ac_unit.glb`, w: 0.9 }, // PA5 Split de aire acondicionado (muro)
  andon_light: { url: `${DIR}/andon_light.glb`, w: 0.3 }, // CO5 Torre ANDON / stack light
  binder: { url: `${DIR}/binder.glb`, w: 0.28 }, // CO8 Carpeta / archivador cGMP
  blueprint_roll: { url: `${DIR}/blueprint_roll.glb`, w: 0.5 }, // G17 Rollo de planos
  bottle: { url: `${DIR}/bottle.glb`, w: 0.12 }, // D09 Botella (Inca Kola)
  bread: { url: `${DIR}/bread.glb`, w: 0.2 }, // GM3 Pan
  cable_reel: { url: `${DIR}/cable_reel.glb`, w: 0.4 }, // C05 Bobina de cable
  calculator: { url: `${DIR}/calculator.glb`, w: 0.18 }, // G10 Calculadora de escritorio
  cardboard_box: { url: `${DIR}/cardboard_box.glb`, w: 0.5 }, // G26 Caja de carton / crate
  chair_office: { url: `${DIR}/chair_office.glb`, w: 0.52 }, // G02 Silla de oficina de trabajo
  coffee_mug: { url: `${DIR}/coffee_mug.glb`, w: 0.12 }, // G13 Taza de cafe / mug
  coin: { url: `${DIR}/coin.glb`, w: 0.4 }, // DE2 Moneda / pila de monedas
  computer_tower: { url: `${DIR}/computer_tower.glb`, w: 0.24 }, // G05 Torre de PC / gabinete
  construction_sign: { url: `${DIR}/construction_sign.glb`, w: 0.9 }, // IA4 Valla / senal de obra
  cooking_pot: { url: `${DIR}/cooking_pot.glb`, w: 0.3 }, // D04 Olla de cocina
  cork_board: { url: `${DIR}/cork_board.glb`, w: 1.0 }, // AS3 Cartelera de corcho
  credit_card: { url: `${DIR}/credit_card.glb`, w: 0.09 }, // G24 Tarjeta bancaria / credito
  crt_monitor: { url: `${DIR}/crt_monitor.glb`, w: 0.5 }, // A03 Monitor CRT retro
  // G01 Escritorio de oficina. OJO: desk_office.glb (= school_desk.glb) del
  // pack es en realidad un BAUL/cofre macizo (se ve como caja solida), NO un
  // escritorio. Se apunta a wooden_desk.glb, que si tiene superficie + patas.
  desk_office: { url: `${DIR}/wooden_desk.glb`, w: 1.15 },
  dining_chair: { url: `${DIR}/dining_chair.glb`, w: 0.5 }, // D07 Silla de comensal
  display_case: { url: `${DIR}/display_case.glb`, w: 1.2 }, // GM1 Vitrina de cafeteria
  donut: { url: `${DIR}/donut.glb`, w: 0.15 }, // GM2 Dona
  envelope: { url: `${DIR}/envelope.glb`, w: 0.24 }, // G25 Sobre de papel
  examination_table: { url: `${DIR}/examination_table.glb`, w: 1.6 }, // I01 Camilla
  filing_cabinet: { url: `${DIR}/filing_cabinet.glb`, w: 0.6 }, // G08 Archivador metalico
  flat_file_cabinet: { url: `${DIR}/flat_file_cabinet.glb`, w: 1.0 }, // IA2 Planoteca
  garbage_bag: { url: `${DIR}/garbage_bag.glb`, w: 0.4 }, // GM8 Bolsa negra de basura
  kitchen_counter: { url: `${DIR}/kitchen_counter.glb`, w: 1.6 }, // D01 Mesada de cocina
  lab_table: { url: `${DIR}/lab_table.glb`, w: 1.4 }, // CO6 Mesa QC / lab bench
  laptop: { url: `${DIR}/laptop.glb`, w: 0.4 }, // G03 Laptop (carcasa; pantalla Canvas)
  magnifying_lamp: { url: `${DIR}/magnifying_lamp.glb`, w: 0.4 }, // CO7 Lupa de inspeccion
  manila_folder: { url: `${DIR}/manila_folder.glb`, w: 0.28 }, // G16 Carpeta manila
  medical_cross: { url: `${DIR}/medical_cross.glb`, w: 0.4 }, // I07 Cruz medica roja
  medicine_box: { url: `${DIR}/medicine_box.glb`, w: 0.24 }, // I06 Caja de medicamentos
  meeting_table: { url: `${DIR}/meeting_table.glb`, w: 1.6 }, // DE4 Mesa de reunion
  monitor: { url: `${DIR}/monitor.glb`, w: 0.5 }, // G04 Monitor de escritorio (carcasa)
  notebook: { url: `${DIR}/notebook.glb`, w: 0.3 }, // AS4 Cuaderno de inventario
  old_radio: { url: `${DIR}/old_radio.glb`, w: 0.3 }, // C03 Radio base antigua
  paper_bag: { url: `${DIR}/paper_bag.glb`, w: 0.25 }, // GM5 Bolsa kraft / Good Bag
  paper_stack: { url: `${DIR}/paper_stack.glb`, w: 0.35 }, // G15 Pila de papeles
  pedestal: { url: `${DIR}/pedestal.glb`, w: 0.5 }, // DE5 Pedestal / podio
  pedestal_fan: { url: `${DIR}/pedestal_fan.glb`, w: 0.4 }, // IA5 Ventilador de pie
  pizza: { url: `${DIR}/pizza.glb`, w: 0.35 }, // GM4 Pizza
  plate: { url: `${DIR}/plate.glb`, w: 0.25 }, // D08 Plato de comida
  potted_plant: { url: `${DIR}/potted_plant.glb`, w: 0.5 }, // G21 Maceta con planta
  projection_screen: { url: `${DIR}/projection_screen.glb`, w: 1.6 }, // AS2 Pantalla proy.
  projector: { url: `${DIR}/projector.glb`, w: 0.4 }, // AS1 Proyector con lente
  range_hood: { url: `${DIR}/range_hood.glb`, w: 1.0 }, // D03 Campana extractora
  reception_counter: { url: `${DIR}/reception_counter.glb`, w: 1.6 }, // G09 Mostrador
  restaurant_table: { url: `${DIR}/restaurant_table.glb`, w: 1.0 }, // D06 Mesa restaurante
  school_chair: { url: `${DIR}/school_chair.glb`, w: 0.5 }, // A02 Silla escolar madera
  // A01 Pupitre escolar. school_desk.glb del pack es un BAUL/cofre macizo (no
  // un pupitre); se apunta a wooden_desk.glb (escritorio real de patas).
  school_desk: { url: `${DIR}/wooden_desk.glb`, w: 1.05 },
  scifi_door: { url: `${DIR}/scifi_door.glb`, w: 1.2 }, // F01 Puerta futurista
  service_cart: { url: `${DIR}/service_cart.glb`, w: 0.9 }, // GM7 Carro de desechos
  shelf: { url: `${DIR}/shelf.glb`, w: 0.9 }, // G07 Estanteria metalica
  smartphone: { url: `${DIR}/smartphone.glb`, w: 0.09 }, // G23 Smartphone (carcasa)
  space_chair: { url: `${DIR}/space_chair.glb`, w: 0.7 }, // F03 Silla sci-fi
  space_table: { url: `${DIR}/space_table.glb`, w: 1.2 }, // F02 Escritorio sci-fi
  stove: { url: `${DIR}/stove.glb`, w: 1.0 }, // D02 Hornillas / cocina
  tablet: { url: `${DIR}/tablet.glb`, w: 0.24 }, // D10 Tablet de pedidos
  tatami: { url: `${DIR}/tatami.glb`, w: 1.0 }, // PA1 Tatami / colchoneta de dojo
  thermal_printer: { url: `${DIR}/thermal_printer.glb`, w: 0.3 }, // D05 Impresora termica
  toolbox: { url: `${DIR}/toolbox.glb`, w: 0.5 }, // PA6 Caja de herramientas
  traffic_cone: { url: `${DIR}/traffic_cone.glb`, w: 0.3 }, // G18 Cono de trafico
  trash_can: { url: `${DIR}/trash_can.glb`, w: 0.4 }, // G27 Tacho de basura
  tv_screen: { url: `${DIR}/tv_screen.glb`, w: 1.2 }, // DE6 TV / monitor grande (carcasa)
  vial: { url: `${DIR}/vial.glb`, w: 0.1 }, // CO4 Ampolla / vial ambar
  waiting_chair: { url: `${DIR}/waiting_chair.glb`, w: 0.5 }, // G20 Silla de espera / banca
  walkie_talkie: { url: `${DIR}/walkie_talkie.glb`, w: 0.12 }, // C02 Walkie talkie
  wall_clock: { url: `${DIR}/wall_clock.glb`, w: 0.5 }, // G06 Reloj de pared (aguja gira)
  wooden_chair: { url: `${DIR}/wooden_chair.glb`, w: 0.6 }, // PA4 Silla de madera
  wooden_desk: { url: `${DIR}/wooden_desk.glb`, w: 1.1 }, // PA3 Escritorio de madera
  work_table: { url: `${DIR}/work_table.glb`, w: 1.4 }, // IA1 Meson de planos
} as const satisfies Record<string, PropEntry>

export type PropId = keyof typeof PROPS

/** Opciones de colocacion de un prop del catalogo (envuelve placeFurniture). */
export interface PlacePropOpts {
  x: number
  z: number
  /** Altura del grupo (default 0 = piso). Para props sobre un mueble. */
  y?: number
  rotationY?: number
  /** Sobreescribe el ancho por defecto del catalogo. */
  width?: number
  /** Color plano que tinta TODO el modelo (ej. sepia en los pastes). */
  color?: string
  /** Recolor por nombre de material del pack. */
  tint?: Record<string, string>
  /** Contorno de tinta (default true, hoy no-op tras el giro visual). */
  outline?: boolean
}

/**
 * @function placeProp
 * @description Coloca un prop del catalogo por su id, devolviendo el `Group`
 *   posicionado de inmediato (el GLB se carga async, igual que
 *   placeFurniture). El ancho por defecto viene del catalogo salvo override.
 *   Se llama `placeProp` (no `prop`) para no colisionar con la variable
 *   `prop` del loop `addProps` que usan las salas.
 *
 * @example
 *   group.add(placeProp('desk_office', { x: 2, z: room.z }))
 *   group.add(placeProp('vial', { x, z, color: '#c8a878' }))  // sepia paste
 */
export function placeProp(id: PropId, opts: PlacePropOpts): Group {
  const entry = PROPS[id]
  const furnitureOpts: FurnitureOpts = {
    url: entry.url,
    x: opts.x,
    z: opts.z,
    y: opts.y,
    rotationY: opts.rotationY,
    targetWidth: opts.width ?? entry.w,
    color: opts.color,
    tint: opts.tint,
    outline: opts.outline,
  }
  return placeFurniture(furnitureOpts)
}
