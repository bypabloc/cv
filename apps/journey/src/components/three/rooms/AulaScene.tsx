/**
 * @component AulaScene
 * @description Sala 0 — Aula/Universidad (iai + projects-degrees, 2015).
 *   Pupitres con PCs en red, pizarra de RETOS, cuaderno de APRENDIZAJES,
 *   guiño cliente-servidor y micro-interaccion "pasar los proyectos de
 *   bloqueado a listo". Portal al pasado: las tesis bloqueadas.
 */
import { Text } from '@react-three/drei'
import { useMemo, useState } from 'react'
import { useJourneyStore } from '../../../lib/store'
import { Npc } from '../Npc'
import { TEXT_FONT } from '../text-font'
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
  es: 'Reencaminar los proyectos',
  en: 'Rescue the projects',
} as const

/** Micro-interaccion: dos proyectos pasan de BLOQUEADO (rojo) a LISTO. */
function ProjectsBoard({
  position,
  roomIndex,
}: {
  position: [number, number, number]
  roomIndex: number
}) {
  const locale = useJourneyStore((s) => s.locale)
  const [rescued, setRescued] = useState(false)
  const interactable = useMemo(
    () => ({
      id: `micro-aula-${roomIndex}`,
      x: position[0],
      z: position[2],
      radius: 2,
      label: MICRO_LABEL,
      onActivate: () => setRescued(true),
    }),
    [roomIndex, position],
  )
  useInteractable(interactable, !rescued)

  const color = rescued ? '#3f9d63' : '#b23a3a'
  const caption = rescued
    ? locale === 'es'
      ? 'LISTO'
      : 'DONE'
    : locale === 'es'
      ? 'BLOQUEADO'
      : 'BLOCKED'
  return (
    <group position={position} rotation-y={-Math.PI / 2}>
      {[-0.55, 0.55].map((x) => (
        <group key={x} position={[x, 1.5, 0]}>
          <mesh>
            <boxGeometry args={[0.85, 0.55, 0.05]} />
            <meshStandardMaterial
              color={color}
              emissive={color}
              emissiveIntensity={0.35}
            />
          </mesh>
          <Text
            position={[0, 0, 0.04]}
            fontSize={0.11}
            color="#f5f2e8"
            font={TEXT_FONT}
          >
            {caption}
          </Text>
        </group>
      ))}
    </group>
  )
}

export default function AulaScene({ room }: RoomSceneProps) {
  const pal = PALETTES.aula
  const half = room.width / 2
  const desks: [number, number][] = [
    [-1.4, -1.2],
    [1.4, -1.2],
    [-1.4, 0.6],
    [1.4, 0.6],
  ]

  return (
    <group>
      {/* pupitres con PCs en red local */}
      {desks.map(([x, dz]) => (
        <group key={`${x}:${dz}`} position={[x, 0, room.z + dz]}>
          <Desk position={[0, 0, 0]} width={1.1} color="#5a4632" />
          <Monitor
            position={[0, 0.75, -0.1]}
            lines={['> ping servidor', 'conectado: OK']}
            bg={pal.screenBg}
            fg={pal.screenFg}
            width={0.42}
          />
        </group>
      ))}

      {/* guiño: pizarra cliente-servidor con el plan de rescate */}
      <ScreenPanel
        position={[0, 1.7, room.z + room.depth / 2 - 0.12]}
        rotationY={Math.PI}
        width={2.6}
        height={1.4}
        title="[CLIENTE] <-> [SERVIDOR]"
        lines={[
          'red local del laboratorio',
          'plan de rescate: 1 semana',
          '2 tesis: bloqueado -> listo',
        ]}
        bg="#2e4d3a"
        fg="#d8ecc8"
      />

      {/* RETOS: pizarra en el muro izquierdo */}
      <FichaProp
        roomIndex={room.index}
        kind="retos"
        style="pizarra"
        position={[-half + 0.45, 0, room.z - 1]}
        rotationY={Math.PI / 2}
        accent={pal.accent}
        label={{ es: 'Leer los retos', en: 'Read the challenges' }}
      />

      {/* APRENDIZAJES: cuaderno sobre podio */}
      <FichaProp
        roomIndex={room.index}
        kind="aprendizajes"
        style="cuaderno"
        position={[half - 1.2, 0, room.z + 1.6]}
        accent={pal.accent}
        label={{ es: 'Leer los aprendizajes', en: 'Read the learnings' }}
      />

      {/* micro-interaccion en el muro derecho */}
      <ProjectsBoard
        position={[half - 0.4, 0, room.z - 1]}
        roomIndex={room.index}
      />

      {/* portal al pasado */}
      <PastPortal
        room={room}
        position={[-half + 0.35, 0, room.z + 2.2]}
        rotationY={Math.PI / 2}
        accent={pal.accent}
      />

      {/* NPCs: estudiantes en los pupitres + uno paseando */}
      <Npc
        position={[-1.4, 0, room.z - 0.6]}
        shirt="#7a5c3a"
        rotationY={Math.PI}
      />
      <Npc position={[1.4, 0, room.z + 1.2]} shirt="#4a6a52" rotationY={0.4} />
      <Npc
        position={[0, 0, room.z + 2.6]}
        path={[
          [0, room.z + 2.6],
          [2.2, room.z + 2.6],
          [2.2, room.z - 2.2],
          [-2.4, room.z - 2.2],
        ]}
        shirt="#5a7a9a"
        speed={0.7}
      />
    </group>
  )
}
