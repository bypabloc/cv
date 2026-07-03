/**
 * @component CimaScene
 * @description Sala 8 — LA CIMA (Destacame Fullstack & Lider, CL+MX,
 *   2022-hoy). War room premium azul #0052CC: mesa de reunion, pared de
 *   paneles, grafo de microservicios, orquestacion Chile+Mexico
 *   (micro-interaccion), puerta "Proximamente" y CTA de contacto.
 */
import { Text } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef, useState } from 'react'
import type { MeshStandardMaterial } from 'three'
import { useJourneyStore } from '../../../lib/store'
import { Npc } from '../Npc'
import { makeCanvasTexture } from '../textures'
import { useInteractable } from '../use-interactable'
import { PALETTES } from './palettes'
import {
  Desk,
  FichaProp,
  Monitor,
  PastPortal,
  type RoomSceneProps,
  ScreenPanel,
} from './shared'

const MICRO_LABEL = {
  es: 'Orquestar Chile + Mexico',
  en: 'Orchestrate Chile + Mexico',
} as const

const CONTACT_LABEL = {
  es: 'Contactar a Pablo',
  en: 'Contact Pablo',
} as const

/** Micro-interaccion: pulso viajando entre CL y MX via el nodo central. */
function Orchestration({
  position,
  roomIndex,
}: {
  position: [number, number, number]
  roomIndex: number
}) {
  const [pulses, setPulses] = useState(0)
  const clMaterial = useRef<MeshStandardMaterial>(null)
  const mxMaterial = useRef<MeshStandardMaterial>(null)
  const startRef = useRef(0)

  const interactable = useMemo(
    () => ({
      id: `micro-cima-${roomIndex}`,
      x: position[0],
      z: position[2],
      radius: 2.4,
      label: MICRO_LABEL,
      onActivate: () => setPulses((n) => n + 1),
    }),
    [roomIndex, position],
  )
  useInteractable(interactable)

  useFrame(({ clock }) => {
    if (pulses > 0 && startRef.current === 0) {
      startRef.current = clock.elapsedTime
    }
    const t = clock.elapsedTime - startRef.current
    if (pulses === 0 || t > 2.4) {
      startRef.current = 0
      if (pulses > 0) {
        setPulses(0)
      }
      return
    }
    const wave = Math.abs(Math.sin(t * Math.PI * 2))
    if (clMaterial.current) {
      clMaterial.current.emissiveIntensity = 0.4 + wave * 1.4
    }
    if (mxMaterial.current) {
      mxMaterial.current.emissiveIntensity = 0.4 + (1 - wave) * 1.4
    }
  })

  return (
    <group position={position} rotation-y={Math.PI}>
      {/* nodo central (la plataforma) */}
      <mesh position={[0, 1.7, 0]}>
        <icosahedronGeometry args={[0.22, 0]} />
        <meshStandardMaterial
          color="#0052cc"
          emissive="#3a7bff"
          emissiveIntensity={0.8}
        />
      </mesh>
      {/* CL / MX */}
      <mesh position={[-1.1, 1.4, 0]}>
        <sphereGeometry args={[0.16, 14, 14]} />
        <meshStandardMaterial
          ref={clMaterial}
          color="#16324f"
          emissive="#4d9dff"
          emissiveIntensity={0.4}
        />
      </mesh>
      <mesh position={[1.1, 1.4, 0]}>
        <sphereGeometry args={[0.16, 14, 14]} />
        <meshStandardMaterial
          ref={mxMaterial}
          color="#16324f"
          emissive="#4d9dff"
          emissiveIntensity={0.4}
        />
      </mesh>
      <Text position={[-1.1, 1.08, 0]} fontSize={0.12} color="#9db8ff">
        CHILE
      </Text>
      <Text position={[1.1, 1.08, 0]} fontSize={0.12} color="#9db8ff">
        MEXICO
      </Text>
      {/* conexiones */}
      {[-0.55, 0.55].map((x) => (
        <mesh key={x} position={[x, 1.55, 0]} rotation-z={x < 0 ? -0.28 : 0.28}>
          <cylinderGeometry args={[0.015, 0.015, 1.05, 6]} />
          <meshStandardMaterial
            color="#3a7bff"
            emissive="#3a7bff"
            emissiveIntensity={0.5}
          />
        </mesh>
      ))}
    </group>
  )
}

/** CTA de contacto: holograma girando sobre pedestal. */
function ContactBeacon({
  position,
  roomIndex,
}: {
  position: [number, number, number]
  roomIndex: number
}) {
  const openContact = useJourneyStore((s) => s.openContact)
  const holoRef = useRef<MeshStandardMaterial>(null)
  const interactable = useMemo(
    () => ({
      id: `contact-${roomIndex}`,
      x: position[0],
      z: position[2],
      radius: 2.2,
      label: CONTACT_LABEL,
      onActivate: () => openContact(),
    }),
    [roomIndex, position, openContact],
  )
  useInteractable(interactable)

  useFrame(({ clock }) => {
    if (holoRef.current) {
      holoRef.current.emissiveIntensity =
        0.9 + Math.sin(clock.elapsedTime * 2.4) * 0.35
    }
  })

  return (
    <group position={position}>
      <mesh position={[0, 0.5, 0]}>
        <cylinderGeometry args={[0.28, 0.34, 1, 12]} />
        <meshStandardMaterial color="#141a26" roughness={0.5} />
      </mesh>
      <mesh position={[0, 1.35, 0]} rotation-y={0.6}>
        <octahedronGeometry args={[0.24, 0]} />
        <meshStandardMaterial
          ref={holoRef}
          color="#0052cc"
          emissive="#5aa2ff"
          emissiveIntensity={0.9}
          transparent
          opacity={0.92}
        />
      </mesh>
      <pointLight
        position={[0, 1.4, 0]}
        intensity={2.2}
        distance={4}
        color="#5aa2ff"
      />
    </group>
  )
}

/** Grafo de microservicios dibujado en canvas (pared). */
function useGraphTexture() {
  return useMemo(
    () =>
      makeCanvasTexture(512, (ctx, size) => {
        ctx.fillStyle = '#0a1220'
        ctx.fillRect(0, 0, size, size)
        const nodes: [number, number, string][] = [
          [256, 90, 'gateway'],
          [120, 220, 'scoring'],
          [256, 230, 'pagos'],
          [392, 220, 'campanas'],
          [180, 370, 'usuarios'],
          [340, 370, 'deudas'],
        ]
        ctx.strokeStyle = '#2d5bb9'
        ctx.lineWidth = 3
        const edges: [number, number][] = [
          [0, 1],
          [0, 2],
          [0, 3],
          [1, 4],
          [2, 4],
          [2, 5],
          [3, 5],
        ]
        for (const [a, b] of edges) {
          const na = nodes[a]
          const nb = nodes[b]
          if (!na || !nb) {
            continue
          }
          ctx.beginPath()
          ctx.moveTo(na[0], na[1])
          ctx.lineTo(nb[0], nb[1])
          ctx.stroke()
        }
        for (const [x, y, name] of nodes) {
          ctx.fillStyle = '#0f2547'
          ctx.strokeStyle = '#5aa2ff'
          ctx.beginPath()
          ctx.arc(x, y, 34, 0, Math.PI * 2)
          ctx.fill()
          ctx.stroke()
          ctx.fillStyle = '#bcd6ff'
          ctx.font = '18px monospace'
          ctx.textAlign = 'center'
          ctx.fillText(name, x, y + 6)
        }
        ctx.textAlign = 'left'
        ctx.fillStyle = '#5aa2ff'
        ctx.font = 'bold 22px monospace'
        ctx.fillText('django microservices', 24, 470)
      }),
    [],
  )
}

export default function CimaScene({ room }: RoomSceneProps) {
  const pal = PALETTES.cima
  const locale = useJourneyStore((s) => s.locale)
  const half = room.width / 2
  const graphTexture = useGraphTexture()
  const chairs: [number, number][] = [
    [-1.1, -0.9],
    [0, -0.9],
    [1.1, -0.9],
    [-1.1, 0.9],
    [0, 0.9],
    [1.1, 0.9],
  ]

  return (
    <group>
      {/* mesa de reunion + sillas */}
      <group position={[0, 0, room.z + 1.2]}>
        <mesh position={[0, 0.74, 0]}>
          <boxGeometry args={[3.4, 0.07, 1.5]} />
          <meshStandardMaterial
            color="#1b2433"
            roughness={0.4}
            metalness={0.2}
          />
        </mesh>
        {[-1.5, 1.5].map((x) => (
          <mesh key={x} position={[x, 0.37, 0]}>
            <boxGeometry args={[0.12, 0.74, 1.3]} />
            <meshStandardMaterial color="#141a26" />
          </mesh>
        ))}
        {chairs.map(([x, dz]) => (
          <group key={`${x}:${dz}`} position={[x, 0, dz]}>
            <mesh position={[0, 0.45, 0]}>
              <boxGeometry args={[0.44, 0.06, 0.44]} />
              <meshStandardMaterial color="#26303f" />
            </mesh>
            <mesh position={[0, 0.75, dz > 0 ? 0.2 : -0.2]}>
              <boxGeometry args={[0.44, 0.55, 0.05]} />
              <meshStandardMaterial color="#26303f" />
            </mesh>
          </group>
        ))}
      </group>

      {/* pared de paneles: observabilidad + vibe coding */}
      <ScreenPanel
        position={[-2.2, 1.9, room.z + room.depth / 2 - 0.12]}
        rotationY={Math.PI}
        width={2.2}
        height={1.3}
        title="observability"
        lines={[
          'p95: 180ms',
          'uptime: 99.97%',
          'campanas: 4 min (antes: horas)',
        ]}
        bg={pal.screenBg}
        fg={pal.screenFg}
      />
      <ScreenPanel
        position={[2.2, 1.9, room.z + room.depth / 2 - 0.12]}
        rotationY={Math.PI}
        width={2.2}
        height={1.3}
        title="vibe coding"
        lines={[
          '> claude "refactor module"',
          'tests: 128 passed',
          'review: aprobado',
        ]}
        bg={pal.screenBg}
        fg={pal.screenFg}
      />

      {/* grafo de microservicios en el muro izquierdo */}
      <mesh position={[-half + 0.12, 2, room.z - 1]} rotation-y={Math.PI / 2}>
        <planeGeometry args={[2.6, 2.6]} />
        <meshStandardMaterial
          map={graphTexture}
          emissiveMap={graphTexture}
          emissive="#ffffff"
          emissiveIntensity={0.5}
        />
      </mesh>

      {/* setup de escritorio ultrawide */}
      <group position={[half - 1.6, 0, room.z - 2.4]}>
        <Desk position={[0, 0, 0]} width={2} color="#1b2433" />
        <Monitor
          position={[0, 0.75, -0.15]}
          rotationY={0.2}
          title="code base -> forks"
          lines={[
            'santander/',
            'scotiabank/',
            'lider/',
            'mismo DS, N entidades',
          ]}
          bg={pal.screenBg}
          fg={pal.screenFg}
          width={1.1}
        />
      </group>

      {/* micro-interaccion: orquestacion CL+MX */}
      <Orchestration
        position={[0, 0, room.z - room.depth / 2 + 1.4]}
        roomIndex={room.index}
      />

      {/* puerta PROXIMAMENTE al fondo */}
      <group
        position={[half - 0.35, 0, room.z - 1.6]}
        rotation-y={-Math.PI / 2}
      >
        <mesh position={[0, 1.05, 0]}>
          <boxGeometry args={[1.2, 2.1, 0.09]} />
          <meshStandardMaterial color="#10151f" roughness={0.6} />
        </mesh>
        <mesh position={[0, 1.05, 0.05]}>
          <boxGeometry args={[1.05, 1.9, 0.02]} />
          <meshStandardMaterial
            color="#141c2b"
            emissive={pal.accent}
            emissiveIntensity={0.12}
          />
        </mesh>
        <Text position={[0, 1.35, 0.09]} fontSize={0.13} color="#9db8ff">
          {locale === 'es' ? 'PROXIMAMENTE' : 'COMING SOON'}
        </Text>
        <Text position={[0, 1.1, 0.09]} fontSize={0.08} color="#5f77a8">
          {locale === 'es' ? 'ideas futuras' : 'future ideas'}
        </Text>
      </group>

      {/* CTA de contacto junto a la puerta */}
      <ContactBeacon
        position={[half - 1.3, 0, room.z - 0.4]}
        roomIndex={room.index}
      />

      {/* RETOS: pizarra de arquitectura */}
      <FichaProp
        roomIndex={room.index}
        kind="retos"
        style="pizarra"
        position={[-2.6, 0, room.z - room.depth / 2 + 0.5]}
        accent={pal.accent}
        label={{ es: 'Leer los retos', en: 'Read the challenges' }}
      />

      {/* APRENDIZAJES: tablet sobre podio */}
      <FichaProp
        roomIndex={room.index}
        kind="aprendizajes"
        style="cuaderno"
        position={[-half + 1.4, 0, room.z + 2.4]}
        accent={pal.accent}
        label={{ es: 'Leer los aprendizajes', en: 'Read the learnings' }}
      />

      {/* portal al pasado */}
      <PastPortal
        room={room}
        position={[-half + 0.35, 0, room.z + room.depth / 2 - 1.4]}
        rotationY={Math.PI / 2}
        accent={pal.accent}
      />

      {/* NPCs: equipo en reunion + un dev en ronda */}
      <Npc position={[-1.6, 0, room.z + 2.4]} shirt="#24466e" rotationY={0.9} />
      <Npc position={[1.6, 0, room.z + 2.6]} shirt="#3a3f52" rotationY={-1.1} />
      <Npc
        position={[0, 0, room.z - 1]}
        path={[
          [0, room.z - 1],
          [-3, room.z - 3],
          [3.2, room.z - 3.4],
        ]}
        shirt="#0e3a80"
        speed={0.75}
      />

      {/* acento dramatico azul de la CIMA */}
      <pointLight
        position={[0, room.height - 0.6, room.z - 2]}
        intensity={8}
        distance={12}
        decay={1.8}
        color="#3a7bff"
      />
    </group>
  )
}
