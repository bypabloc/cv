/**
 * @component CorpoelecScene
 * @description Sala 1 — CORPOELEC (central electrica estatal, VE, 2013).
 *   Transformador, tablero de medidores, cajas de inventario, monitor con
 *   la tabla jQuery + badge OFFLINE, ventana con torres de alta tension,
 *   casco amarillo. Micro-interaccion: accionar el tablero (rojo -> verde).
 */
import { Text } from '@react-three/drei'
import { useMemo, useState } from 'react'
import { useJourneyStore } from '../../../lib/store'
import { makeCanvasTexture } from '../textures'
import { useInteractable } from '../use-interactable'
import { PALETTES } from './palettes'
import {
  Desk,
  FichaProp,
  Monitor,
  PastPortal,
  type RoomSceneProps,
} from './shared'

const MICRO_LABEL = {
  es: 'Accionar el tablero de control',
  en: 'Operate the control board',
} as const

/** Transformador: caja gris + aletas + 3 bujes ceramicos (primitivas). */
function Transformer({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.7, 0]}>
        <boxGeometry args={[1.3, 1.4, 0.9]} />
        <meshStandardMaterial
          color="#5c6168"
          roughness={0.7}
          metalness={0.35}
        />
      </mesh>
      {[-0.5, 0, 0.5].map((x) => (
        <group key={x} position={[x, 1.55, 0]}>
          <mesh>
            <cylinderGeometry args={[0.07, 0.09, 0.35, 10]} />
            <meshStandardMaterial color="#b8b4a8" roughness={0.5} />
          </mesh>
        </group>
      ))}
      {[-0.72, 0.72].map((x) => (
        <mesh key={x} position={[x, 0.7, 0]}>
          <boxGeometry args={[0.12, 1.2, 0.7]} />
          <meshStandardMaterial color="#4c5057" roughness={0.8} />
        </mesh>
      ))}
    </group>
  )
}

/** Micro-interaccion: tablero de medidores rojo -> verde + luz de estado. */
function ControlBoard({
  position,
  roomIndex,
}: {
  position: [number, number, number]
  roomIndex: number
}) {
  const [energized, setEnergized] = useState(false)
  const interactable = useMemo(
    () => ({
      id: `micro-corpoelec-${roomIndex}`,
      x: position[0],
      z: position[2],
      radius: 2,
      label: MICRO_LABEL,
      onActivate: () => setEnergized(true),
    }),
    [roomIndex, position],
  )
  useInteractable(interactable, !energized)

  const color = energized ? '#4dcc7a' : '#cc3b3b'
  return (
    <group position={position} rotation-y={Math.PI / 2}>
      <mesh position={[0, 1.5, 0]}>
        <boxGeometry args={[1.6, 1.1, 0.08]} />
        <meshStandardMaterial color="#2e3238" roughness={0.6} />
      </mesh>
      {[-0.5, 0, 0.5].map((x) => (
        <mesh key={x} position={[x, 1.72, 0.06]}>
          <cylinderGeometry args={[0.11, 0.11, 0.03, 14]} />
          <meshStandardMaterial
            color="#d8d4c8"
            emissive={color}
            emissiveIntensity={0.35}
          />
        </mesh>
      ))}
      {[-0.5, 0, 0.5].map((x) => (
        <mesh key={`lamp-${x}`} position={[x, 1.28, 0.06]}>
          <sphereGeometry args={[0.05, 10, 10]} />
          <meshStandardMaterial
            color={color}
            emissive={color}
            emissiveIntensity={1.2}
          />
        </mesh>
      ))}
      <pointLight
        position={[0, 1.5, 0.5]}
        intensity={1.6}
        distance={4}
        color={color}
      />
    </group>
  )
}

/** Ventana con torres de alta tension (silueta dibujada en canvas). */
function TowersWindow({ position }: { position: [number, number, number] }) {
  const texture = useMemo(
    () =>
      makeCanvasTexture(256, (ctx, size) => {
        const sky = ctx.createLinearGradient(0, 0, 0, size)
        sky.addColorStop(0, '#5a6a85')
        sky.addColorStop(1, '#c88d5a')
        ctx.fillStyle = sky
        ctx.fillRect(0, 0, size, size)
        ctx.strokeStyle = '#1c1f26'
        ctx.lineWidth = 3
        for (const cx of [64, 160]) {
          // torre: dos patas + cruces + brazos
          ctx.beginPath()
          ctx.moveTo(cx - 22, size)
          ctx.lineTo(cx, 60)
          ctx.lineTo(cx + 22, size)
          ctx.moveTo(cx - 26, 110)
          ctx.lineTo(cx + 26, 110)
          ctx.moveTo(cx - 18, 80)
          ctx.lineTo(cx + 18, 80)
          ctx.stroke()
        }
        // cables
        ctx.beginPath()
        ctx.moveTo(38, 112)
        ctx.quadraticCurveTo(112, 150, 186, 112)
        ctx.stroke()
      }),
    [],
  )
  return (
    <group position={position} rotation-y={-Math.PI / 2}>
      <mesh>
        <planeGeometry args={[1.8, 1.2]} />
        <meshStandardMaterial
          map={texture}
          emissiveMap={texture}
          emissive="#ffffff"
          emissiveIntensity={0.5}
        />
      </mesh>
      <mesh position={[0, 0, -0.03]}>
        <boxGeometry args={[2, 1.4, 0.05]} />
        <meshStandardMaterial color="#2a2d33" />
      </mesh>
    </group>
  )
}

export default function CorpoelecScene({ room }: RoomSceneProps) {
  const pal = PALETTES.corpoelec
  const locale = useJourneyStore((s) => s.locale)
  const half = room.width / 2
  const crates: [number, number, number][] = [
    [half - 1, 0.3, room.z - 2.6],
    [half - 1.7, 0.3, room.z - 2.4],
    [half - 1, 0.9, room.z - 2.6],
    [half - 1.1, 0.3, room.z - 1.7],
  ]

  return (
    <group>
      <Transformer position={[-half + 1.4, 0, room.z - 2.2]} />

      {/* cajas de inventario con etiqueta */}
      {crates.map(([x, y, z]) => (
        <mesh key={`${x}:${y}:${z}`} position={[x, y, z]}>
          <boxGeometry args={[0.6, 0.6, 0.6]} />
          <meshStandardMaterial color="#8a6f4d" roughness={0.9} />
        </mesh>
      ))}
      <Text
        position={[half - 1, 1.35, room.z - 2.6]}
        fontSize={0.09}
        color="#f2b705"
        anchorX="center"
      >
        {locale === 'es' ? 'INVENTARIO' : 'INVENTORY'}
      </Text>

      {/* monitor con la tabla de inventario + badge OFFLINE */}
      <group position={[0.6, 0, room.z + 2.4]}>
        <Desk position={[0, 0, 0]} width={1.4} color="#3a3e44" />
        <Monitor
          position={[0, 0.75, -0.1]}
          rotationY={Math.PI}
          title="[OFFLINE] inventario"
          lines={[
            'ID    EQUIPO       SEDE',
            '0041  transformador yaracuy',
            '0042  aislador      carabobo',
            '0043  medidor       lara',
            'busqueda: inmediata',
          ]}
          bg={pal.screenBg}
          fg={pal.screenFg}
          width={0.72}
        />
      </group>

      {/* ventana con torres + casco de seguridad */}
      <TowersWindow position={[half - 0.42, 1.7, room.z + 0.8]} />
      <group position={[0.9, 0.85, room.z + 2.1]}>
        <mesh>
          <sphereGeometry
            args={[0.16, 14, 10, 0, Math.PI * 2, 0, Math.PI / 2]}
          />
          <meshStandardMaterial color="#f2b705" roughness={0.5} />
        </mesh>
        <mesh position={[0, 0.005, 0]}>
          <cylinderGeometry args={[0.22, 0.22, 0.02, 14]} />
          <meshStandardMaterial color="#f2b705" roughness={0.5} />
        </mesh>
      </group>

      {/* guiño geografico discreto */}
      <Text
        position={[-half + 0.3, 2.1, room.z + 1.6]}
        rotation-y={Math.PI / 2}
        fontSize={0.14}
        color={pal.accent}
      >
        YARACUY · CARABOBO · LARA
      </Text>

      {/* micro-interaccion: tablero */}
      <ControlBoard
        position={[-half + 0.42, 0, room.z + 1.6]}
        roomIndex={room.index}
      />

      {/* RETOS: pizarra de paradas */}
      <FichaProp
        roomIndex={room.index}
        kind="retos"
        style="pizarra"
        position={[-1.6, 0, room.z + room.depth / 2 - 0.5]}
        rotationY={Math.PI}
        accent={pal.accent}
        label={{ es: 'Leer los retos', en: 'Read the challenges' }}
      />

      {/* APRENDIZAJES: cuaderno de campo */}
      <FichaProp
        roomIndex={room.index}
        kind="aprendizajes"
        style="cuaderno"
        position={[1.9, 0, room.z - 0.6]}
        accent={pal.accent}
        label={{ es: 'Leer los aprendizajes', en: 'Read the learnings' }}
      />

      {/* portal al pasado */}
      <PastPortal
        room={room}
        position={[half - 0.35, 0, room.z + 2.6]}
        rotationY={-Math.PI / 2}
        accent={pal.accent}
      />
    </group>
  )
}
