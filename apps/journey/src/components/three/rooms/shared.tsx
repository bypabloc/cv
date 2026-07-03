/**
 * @module shared (rooms)
 * @description Props procedurales compartidos entre salas: pantallas con
 *   texto canvas, ficha (cuaderno/pizarra) interactuable, portal al pasado
 *   y mobiliario minimo. Todo primitivas — cero .glb.
 */
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import type { Group, MeshStandardMaterial } from 'three'
import type { RoomLayout } from '../../../lib/layout'
import { PAST_OFFSET_X } from '../../../lib/layout'
import type { RoomDef } from '../../../lib/rooms'
import type { FichaKind } from '../../../lib/store'
import { useJourneyStore } from '../../../lib/store'
import { makeCanvasTexture } from '../textures'
import { useInteractable } from '../use-interactable'

/** Contrato de toda escena de sala (T5a/b/c — worktree-safe por diseño). */
export interface RoomSceneProps {
  room: RoomLayout
  def: RoomDef
}

/** Textura de "pantalla"/tablero: lineas de texto sobre fondo plano. */
export function useTextPanelTexture(
  lines: readonly string[],
  bg: string,
  fg: string,
  title?: string,
) {
  return useMemo(
    () =>
      makeCanvasTexture(512, (ctx, size) => {
        ctx.fillStyle = bg
        ctx.fillRect(0, 0, size, size)
        ctx.strokeStyle = fg
        ctx.globalAlpha = 0.25
        ctx.strokeRect(10, 10, size - 20, size - 20)
        ctx.globalAlpha = 1
        ctx.fillStyle = fg
        let y = 64
        if (title) {
          ctx.font = 'bold 34px monospace'
          ctx.fillText(title, 28, y)
          y += 52
        }
        ctx.font = '24px monospace'
        for (const line of lines.slice(0, 12)) {
          ctx.fillText(line.slice(0, 34), 28, y)
          y += 36
        }
      }),
    [lines, bg, fg, title],
  )
}

interface ScreenPanelProps {
  position: [number, number, number]
  rotationY?: number
  width: number
  height: number
  lines: readonly string[]
  bg: string
  fg: string
  title?: string
}

/** Plane emisivo tipo monitor/pizarra con contenido dibujado en canvas. */
export function ScreenPanel({
  position,
  rotationY = 0,
  width,
  height,
  lines,
  bg,
  fg,
  title,
}: ScreenPanelProps) {
  const texture = useTextPanelTexture(lines, bg, fg, title)
  return (
    <mesh position={position} rotation-y={rotationY}>
      <planeGeometry args={[width, height]} />
      <meshStandardMaterial
        map={texture}
        emissiveMap={texture}
        emissive="#ffffff"
        emissiveIntensity={0.55}
      />
    </mesh>
  )
}

interface FichaPropProps {
  roomIndex: number
  kind: FichaKind
  style: 'pizarra' | 'cuaderno'
  position: [number, number, number]
  rotationY?: number
  accent: string
  label: Record<'es' | 'en', string>
}

/**
 * Objeto focal de RETOS (pizarra) o APRENDIZAJES (cuaderno): al acercarse
 * y pulsar E abre la ficha HTML del HUD. Pulsa emisivo cuando esta activo.
 */
export function FichaProp({
  roomIndex,
  kind,
  style,
  position,
  rotationY = 0,
  accent,
  label,
}: FichaPropProps) {
  const openFicha = useJourneyStore((s) => s.openFicha)
  const id = `ficha-${roomIndex}-${kind}`
  const isActive = useJourneyStore((s) => s.activeInteractableId === id)
  const materialRef = useRef<MeshStandardMaterial>(null)

  const interactable = useMemo(
    () => ({
      id,
      x: position[0],
      z: position[2],
      radius: 2.2,
      label,
      onActivate: () => openFicha(roomIndex, kind),
    }),
    [id, position, label, openFicha, roomIndex, kind],
  )
  useInteractable(interactable)

  useFrame(({ clock }) => {
    const material = materialRef.current
    if (!material) {
      return
    }
    material.emissiveIntensity = isActive
      ? 0.45 + Math.sin(clock.elapsedTime * 5) * 0.2
      : 0.12
  })

  if (style === 'pizarra') {
    return (
      <group position={position} rotation-y={rotationY}>
        <mesh position={[0, 1.6, 0]}>
          <boxGeometry args={[1.9, 1.2, 0.06]} />
          <meshStandardMaterial
            ref={materialRef}
            color="#2e4d3a"
            emissive={accent}
            emissiveIntensity={0.12}
          />
        </mesh>
        <mesh position={[0, 1.6, -0.05]}>
          <boxGeometry args={[2.05, 1.35, 0.04]} />
          <meshStandardMaterial color="#5a4632" roughness={0.85} />
        </mesh>
      </group>
    )
  }
  return (
    <group position={position} rotation-y={rotationY}>
      {/* podio + cuaderno abierto */}
      <mesh position={[0, 0.5, 0]}>
        <boxGeometry args={[0.42, 1, 0.42]} />
        <meshStandardMaterial color="#4a3b2a" roughness={0.9} />
      </mesh>
      <mesh position={[-0.14, 1.03, 0]} rotation-z={0.16}>
        <boxGeometry args={[0.3, 0.03, 0.42]} />
        <meshStandardMaterial
          ref={materialRef}
          color="#f2ead8"
          emissive={accent}
          emissiveIntensity={0.12}
        />
      </mesh>
      <mesh position={[0.14, 1.03, 0]} rotation-z={-0.16}>
        <boxGeometry args={[0.3, 0.03, 0.42]} />
        <meshStandardMaterial color="#e8dfc8" />
      </mesh>
    </group>
  )
}

const PORTAL_LABEL = {
  es: 'Cruzar al pasado',
  en: 'Step into the past',
} as const

const EXIT_LABEL = {
  es: 'Volver al presente',
  en: 'Return to the present',
} as const

interface PastPortalProps {
  room: RoomLayout
  position: [number, number, number]
  rotationY?: number
  accent: string
}

/** Puerta-portal al "antes" de la sala: teleporta a la sala espejo sepia. */
export function PastPortal({
  room,
  position,
  rotationY = 0,
  accent,
}: PastPortalProps) {
  const enterPast = useJourneyStore((s) => s.enterPast)
  const swirlRef = useRef<Group>(null)

  const interactable = useMemo(
    () => ({
      id: `portal-${room.index}`,
      x: position[0],
      z: position[2],
      radius: 2,
      label: PORTAL_LABEL,
      onActivate: () =>
        enterPast(room.index, { x: PAST_OFFSET_X, z: room.z + 1.6 }),
    }),
    [room.index, room.z, position, enterPast],
  )
  useInteractable(interactable)

  useFrame(({ clock }) => {
    const swirl = swirlRef.current
    if (swirl) {
      swirl.rotation.z = clock.elapsedTime * 0.9
    }
  })

  return (
    <group position={position} rotation-y={rotationY}>
      <mesh position={[0, 1.05, 0]}>
        <boxGeometry args={[1.3, 2.1, 0.08]} />
        <meshStandardMaterial color="#141018" roughness={0.6} />
      </mesh>
      <group ref={swirlRef} position={[0, 1.05, 0.06]}>
        <mesh>
          <ringGeometry args={[0.32, 0.55, 24]} />
          <meshStandardMaterial
            color={accent}
            emissive={accent}
            emissiveIntensity={1.1}
            transparent
            opacity={0.85}
          />
        </mesh>
      </group>
      <mesh position={[0, 2.28, 0]}>
        <boxGeometry args={[1.5, 0.16, 0.12]} />
        <meshStandardMaterial
          color={accent}
          emissive={accent}
          emissiveIntensity={0.5}
        />
      </mesh>
    </group>
  )
}

interface ExitPortalProps {
  roomIndex: number
  position: [number, number, number]
  returnTo: { x: number; z: number }
}

/** Portal de salida dentro de la sala del pasado. */
export function ExitPortal({ roomIndex, position, returnTo }: ExitPortalProps) {
  const exitPast = useJourneyStore((s) => s.exitPast)
  const interactable = useMemo(
    () => ({
      id: `portal-exit-${roomIndex}`,
      x: position[0],
      z: position[2],
      radius: 2,
      label: EXIT_LABEL,
      onActivate: () => exitPast(returnTo),
    }),
    [roomIndex, position, returnTo, exitPast],
  )
  useInteractable(interactable)

  return (
    <group position={position}>
      <mesh position={[0, 1.05, 0]}>
        <boxGeometry args={[1.3, 2.1, 0.08]} />
        <meshStandardMaterial
          color="#1a1a22"
          emissive="#8fd4ff"
          emissiveIntensity={0.4}
        />
      </mesh>
    </group>
  )
}

interface DeskProps {
  position: [number, number, number]
  rotationY?: number
  width?: number
  color?: string
}

/** Escritorio/mesa minima: tapa + 2 patas laterales. */
export function Desk({
  position,
  rotationY = 0,
  width = 1.2,
  color = '#4a4038',
}: DeskProps) {
  return (
    <group position={position} rotation-y={rotationY}>
      <mesh position={[0, 0.72, 0]}>
        <boxGeometry args={[width, 0.05, 0.6]} />
        <meshStandardMaterial color={color} roughness={0.85} />
      </mesh>
      <mesh position={[-width / 2 + 0.05, 0.36, 0]}>
        <boxGeometry args={[0.06, 0.72, 0.55]} />
        <meshStandardMaterial color={color} roughness={0.85} />
      </mesh>
      <mesh position={[width / 2 - 0.05, 0.36, 0]}>
        <boxGeometry args={[0.06, 0.72, 0.55]} />
        <meshStandardMaterial color={color} roughness={0.85} />
      </mesh>
    </group>
  )
}

interface MonitorProps {
  position: [number, number, number]
  rotationY?: number
  lines: readonly string[]
  bg: string
  fg: string
  title?: string
  width?: number
}

/** Monitor sobre pie con pantalla canvas emisiva. */
export function Monitor({
  position,
  rotationY = 0,
  lines,
  bg,
  fg,
  title,
  width = 0.6,
}: MonitorProps) {
  const height = width * 0.6
  return (
    <group position={position} rotation-y={rotationY}>
      <mesh position={[0, 0.06, 0]}>
        <cylinderGeometry args={[0.09, 0.12, 0.12, 10]} />
        <meshStandardMaterial color="#1c1c20" />
      </mesh>
      <mesh position={[0, height / 2 + 0.14, -0.02]}>
        <boxGeometry args={[width + 0.05, height + 0.05, 0.05]} />
        <meshStandardMaterial color="#15151a" />
      </mesh>
      <ScreenPanel
        position={[0, height / 2 + 0.14, 0.01]}
        width={width}
        height={height}
        lines={lines}
        bg={bg}
        fg={fg}
        title={title}
      />
    </group>
  )
}

/** Pila de papeles: laminas blancas apiladas con leve desorden. */
export function PaperStack({
  position,
  count = 8,
}: {
  position: [number, number, number]
  count?: number
}) {
  const sheets = useMemo(
    () =>
      Array.from({ length: count }, (_, i) => ({
        y: 0.012 * i,
        rot: Math.sin(i * 2.3) * 0.25,
      })),
    [count],
  )
  return (
    <group position={position}>
      {sheets.map((sheet) => (
        <mesh key={sheet.y} position={[0, sheet.y, 0]} rotation-y={sheet.rot}>
          <boxGeometry args={[0.3, 0.012, 0.42]} />
          <meshStandardMaterial color="#e8e2d0" roughness={0.9} />
        </mesh>
      ))}
    </group>
  )
}
