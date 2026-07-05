/**
 * @module themes (engine)
 * @description Paletas manga-ink por zona (sala/pasillo/pasado): colores
 *   planos de alto contraste, tinta, escalones del toon shading y colores
 *   de fog/sky que el zone manager aplica al cambiar de zona. Evolucion de
 *   `rooms/palettes.ts` subiendo contraste y saturacion (decision 5 del
 *   plan journey-vanilla-manga).
 *
 *   Nota DS: son colores de MATERIAL WebGL/canvas, no CSS del UI — los
 *   tokens var(--color-*) no aplican dentro del renderer.
 */
import type { RoomId } from '../lib/rooms'

export type ThemeZoneId = RoomId | 'corridor' | 'past'

export interface RoomTheme {
  /** Color plano base de los muros. */
  wall: string
  /** Color plano base del piso. */
  floor: string
  /** Tinta de los trazos (lineas wobbly, hatching, zocalo). */
  ink: string
  /** Acento de la sala (fichas, portal, micro-interaccion). */
  accent: string
  /** Guiño secundario (zocalo de muros, marcos de pizarras). Default: ink. */
  trim?: string
  /** Color de la luz principal de la zona. */
  lightColor: string
  /** Niebla de la zona (lerp al entrar). */
  fog: string
  /** scene.background de la zona. */
  sky: string
  /** Escalones sombra->luz del gradient map toon (3, alto contraste). */
  gradient: readonly [string, string, string]
  /** Fondo/tinta de pantallas y paneles canvas. */
  screenBg: string
  screenFg: string
}

export const THEMES: Record<ThemeZoneId, RoomTheme> = {
  // aula: paredes blancas + piso beige, acento AZUL y guiños MORADOS
  // (zocalo/marcos via trim) — decision del usuario 2026-07-04
  aula: {
    wall: '#eae6dc',
    floor: '#d8c6a0',
    ink: '#232840',
    accent: '#2f6fd0',
    trim: '#7a4fc0',
    lightColor: '#dfe9ff',
    fog: '#141722',
    sky: '#181c2a',
    gradient: ['#7d829a', '#c2c8da', '#ffffff'],
    screenBg: '#101c34',
    screenFg: '#8fb8ff',
  },
  // corpoelec: grises industriales frios + naranja + amarillo seguridad
  corpoelec: {
    wall: '#454b54',
    floor: '#33373c',
    ink: '#121418',
    accent: '#e2572b',
    lightColor: '#e6ecff',
    fog: '#101216',
    sky: '#14171c',
    gradient: ['#383e48', '#8b93a2', '#eef2f8'],
    screenBg: '#0f1822',
    screenFg: '#84e0a0',
  },
  // ipasme: clinico, azul institucional + verde menta
  ipasme: {
    wall: '#f2f0eb',
    floor: '#dbe8e4',
    ink: '#1c2a30',
    accent: '#2f7fb0',
    trim: '#7ecab0',
    lightColor: '#f2f8ff',
    fog: '#d8e2e4',
    sky: '#e4ecee',
    gradient: ['#7f949c', '#c4d4d8', '#ffffff'],
    screenBg: '#0e1e2c',
    screenFg: '#7ec8e8',
  },
  // cofasa: sala limpia farma, azul Cofasa + grises (andon solo en su prop)
  cofasa: {
    wall: '#f2f0eb',
    floor: '#dfe4ea',
    ink: '#182430',
    accent: '#1f6fb0',
    trim: '#c8ccd2',
    lightColor: '#f4f7fb',
    fog: '#d9dee6',
    sky: '#e6eaf0',
    gradient: ['#848d9a', '#c6cdd8', '#ffffff'],
    screenBg: '#101a26',
    screenFg: '#6fb8e8',
  },
  // dibal: restaurante + POS, navy + teal Dibal
  dibal: {
    wall: '#f2f0eb',
    floor: '#d6dee0',
    ink: '#101c22',
    accent: '#1f8f8a',
    trim: '#1b2433',
    lightColor: '#f2f6f6',
    fog: '#d6dedf',
    sky: '#e2eaea',
    gradient: ['#7e8e90', '#c2d0d0', '#ffffff'],
    screenBg: '#0c1a22',
    screenFg: '#5fd8c8',
  },
  // goodmeal: food-tech, teal GoodMeal + kraft
  goodmeal: {
    wall: '#f2f0eb',
    floor: '#e2ddc8',
    ink: '#1c241c',
    accent: '#1fa08a',
    trim: '#c8a86a',
    lightColor: '#f4f8f2',
    fog: '#dee2d6',
    sky: '#e8ecdf',
    gradient: ['#8a9184', '#ccd2c4', '#ffffff'],
    screenBg: '#0e2018',
    screenFg: '#5fd8a8',
  },
  // destacame (ex-cima): azul Destacame sobre casi-negro (C3 lo pasa a
  // paredes blancas segun la tabla del canon)
  destacame: {
    wall: '#1d2942',
    floor: '#161d2c',
    ink: '#080c16',
    accent: '#0052cc',
    lightColor: '#9db8ff',
    fog: '#0a0e16',
    sky: '#0a0e16',
    gradient: ['#1e2840', '#4d6cab', '#d4e2ff'],
    screenBg: '#0a1220',
    screenFg: '#6fa8ff',
  },
  // futuro: vision, azul-violeta neutro premium
  futuro: {
    wall: '#f2f0eb',
    floor: '#d8dce4',
    ink: '#181c30',
    accent: '#5a6ff0',
    trim: '#a0a8d8',
    lightColor: '#eef0ff',
    fog: '#d8dcea',
    sky: '#e4e7f2',
    gradient: ['#7d82a0', '#c2c6e0', '#ffffff'],
    screenBg: '#10142a',
    screenFg: '#8a9aff',
  },
  // pasillo: neutro oscuro desaturado (esclusa entre etapas)
  corridor: {
    wall: '#2e2e38',
    floor: '#26262e',
    ink: '#0e0e14',
    accent: '#8fa3c8',
    lightColor: '#cfd8ff',
    fog: '#0b0b10',
    sky: '#0b0b10',
    gradient: ['#33333e', '#7c7c90', '#eaeaf4'],
    screenBg: '#15151c',
    screenFg: '#aab6d8',
  },
  // pasado: sepia sucio (el filtro CSS remata el look)
  past: {
    wall: '#4a4132',
    floor: '#3a332a',
    ink: '#201a10',
    accent: '#c8a878',
    lightColor: '#e8c89a',
    fog: '#141210',
    sky: '#17140f',
    gradient: ['#403626', '#94805e', '#ecd9b6'],
    screenBg: '#2c2620',
    screenFg: '#b08a6a',
  },
}

/** Captions del portal al pasado (van al HUD como DOM, nunca WebGL). */
export const PAST_CAPTIONS: Record<RoomId, Record<'es' | 'en', string>> = {
  aula: {
    es: 'Antes: karate-do, videojuegos y aires acondicionados — cero codigo',
    en: 'Before: karate-do, video games and AC repair — zero code',
  },
  corpoelec: {
    es: 'Antes: planillas de papel duplicadas en 3 sedes',
    en: 'Before: duplicated paper records across 3 sites',
  },
  ipasme: {
    es: 'Antes: historias medicas en carpetas de papel',
    en: 'Before: medical records in paper folders',
  },
  cofasa: {
    es: 'Antes: paradas de maquina anotadas a mano',
    en: 'Before: machine downtime logged by hand',
  },
  dibal: {
    es: 'Antes: comandas en papelitos y boletas a mano',
    en: 'Before: paper order slips and handwritten receipts',
  },
  goodmeal: {
    es: 'Antes: comida buena al tacho en cada cierre',
    en: 'Before: good food binned at every closing',
  },
  destacame: {
    es: 'Antes: deudas sin gestionar y procesos manuales',
    en: 'Before: unmanaged debts and manual processes',
  },
  // futuro no tiene grieta al pasado: esta caption nunca se muestra
  futuro: {
    es: 'El futuro no tiene un antes',
    en: 'The future has no before',
  },
}

/** Theme de una zona del recorrido (sala por id, pasillo o pasado). */
export function themeFor(zoneId: ThemeZoneId): RoomTheme {
  return THEMES[zoneId]
}
