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
  // aula: papel calido + madera clara, tinta sepia-negra, verde pizarra
  aula: {
    wall: '#5a4c3a',
    floor: '#6b5233',
    ink: '#241a10',
    accent: '#7fb069',
    lightColor: '#ffd9a0',
    fog: '#171310',
    sky: '#1d1712',
    gradient: ['#4a3c2c', '#a8875e', '#f7e9cc'],
    screenBg: '#22331f',
    screenFg: '#c6eab4',
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
  // cima: azul Destacame sobre casi-negro, tinta azul-negra, cian plano
  cima: {
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
  cima: {
    es: 'Antes: procesos manuales y aislados, un solo pais',
    en: 'Before: manual, siloed processes in a single country',
  },
}

/** Theme de una zona del recorrido (sala por id, pasillo o pasado). */
export function themeFor(zoneId: ThemeZoneId): RoomTheme {
  return THEMES[zoneId]
}
