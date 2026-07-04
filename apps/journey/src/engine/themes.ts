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
