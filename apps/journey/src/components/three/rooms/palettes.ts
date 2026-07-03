/**
 * @module palettes
 * @description Paleta por sala (rubro real): 2-4 colores + acento, como
 *   manda el plan. Son colores de material WebGL/canvas (no CSS del UI).
 */
import type { RoomId } from '../../../lib/rooms'

export interface RoomPalette {
  wall: string
  wallSpeck: string
  floor: string
  floorLine: string
  accent: string
  lightColor: string
  screenBg: string
  screenFg: string
}

export const PALETTES: Record<RoomId, RoomPalette> = {
  // aula: madera calida + verde pizarra
  aula: {
    wall: '#494237',
    wallSpeck: '#f5ead0',
    floor: '#57452f',
    floorLine: '#493a27',
    accent: '#7fb069',
    lightColor: '#ffd9a0',
    screenBg: '#22331f',
    screenFg: '#c6eab4',
  },
  // corpoelec: gris industrial + naranja CORPOELEC + amarillo seguridad
  corpoelec: {
    wall: '#3c4046',
    wallSpeck: '#dfe3e8',
    floor: '#33373c',
    floorLine: '#292c30',
    accent: '#e2572b',
    lightColor: '#e6ecff',
    screenBg: '#0f1822',
    screenFg: '#84e0a0',
  },
  // cima: azul Destacame #0052CC premium dramatico
  cima: {
    wall: '#1e2634',
    wallSpeck: '#7fa4ff',
    floor: '#232a34',
    floorLine: '#1a2029',
    accent: '#0052cc',
    lightColor: '#9db8ff',
    screenBg: '#0a1220',
    screenFg: '#6fa8ff',
  },
}

/** Captions del portal al pasado (se muestran en el HUD, DOM real). */
export const PAST_CAPTIONS: Record<RoomId, Record<'es' | 'en', string>> = {
  aula: {
    es: 'Antes: dos proyectos de grado bloqueados por meses',
    en: 'Before: two degree projects stuck for months',
  },
  corpoelec: {
    es: 'Antes: planillas de papel duplicadas en 3 sedes',
    en: 'Before: duplicated paper records across 3 sites',
  },
  cima: {
    es: 'Antes: procesos manuales y aislados, un solo pais',
    en: 'Before: manual, siloed processes in a single country',
  },
}
