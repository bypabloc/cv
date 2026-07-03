/**
 * @component Door
 * @description Puerta con bisagra al final de un pasillo. Interactuable por
 *   proximidad (E / tap): al abrir, anima la rotacion y su bloqueador de
 *   colision desaparece (PlayerControls lo filtra por doorsOpen). Es
 *   bidireccional: queda abierta y se puede volver.
 */
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import type { Group } from 'three'
import { DOOR_HEIGHT, DOOR_WIDTH, type DoorLayout } from '../../lib/layout'
import { useJourneyStore } from '../../lib/store'
import { useInteractable } from './use-interactable'

interface DoorProps {
  door: DoorLayout
}

const JAMB = 0.09

export function Door({ door }: DoorProps) {
  const isOpen = useJourneyStore(
    (s) => s.doorsOpen[door.corridorIndex] === true,
  )
  const openDoor = useJourneyStore((s) => s.openDoor)
  const leafRef = useRef<Group>(null)

  const interactable = useMemo(
    () => ({
      id: `door-${door.corridorIndex}`,
      x: door.x,
      z: door.z,
      radius: 2.1,
      label: { es: 'Abrir la puerta', en: 'Open the door' },
      onActivate: () => openDoor(door.corridorIndex),
    }),
    [door.corridorIndex, door.x, door.z, openDoor],
  )
  useInteractable(interactable, !isOpen)

  useFrame((_, dt) => {
    const leaf = leafRef.current
    if (!leaf) {
      return
    }
    const target = isOpen ? -Math.PI * 0.52 : 0
    leaf.rotation.y += (target - leaf.rotation.y) * Math.min(1, dt * 3.2)
  })

  return (
    <group position={[door.x, 0, door.z]}>
      {/* jambas + dintel del marco */}
      <mesh position={[-DOOR_WIDTH / 2 - JAMB / 2, DOOR_HEIGHT / 2, 0]}>
        <boxGeometry args={[JAMB, DOOR_HEIGHT, 0.22]} />
        <meshStandardMaterial color="#4a3b2a" roughness={0.8} />
      </mesh>
      <mesh position={[DOOR_WIDTH / 2 + JAMB / 2, DOOR_HEIGHT / 2, 0]}>
        <boxGeometry args={[JAMB, DOOR_HEIGHT, 0.22]} />
        <meshStandardMaterial color="#4a3b2a" roughness={0.8} />
      </mesh>
      <mesh position={[0, DOOR_HEIGHT + JAMB / 2, 0]}>
        <boxGeometry args={[DOOR_WIDTH + JAMB * 2, JAMB, 0.22]} />
        <meshStandardMaterial color="#4a3b2a" roughness={0.8} />
      </mesh>
      {/* hoja con bisagra en el borde izquierdo */}
      <group ref={leafRef} position={[-DOOR_WIDTH / 2, 0, 0]}>
        <mesh position={[DOOR_WIDTH / 2, DOOR_HEIGHT / 2, 0]} castShadow>
          <boxGeometry args={[DOOR_WIDTH - 0.02, DOOR_HEIGHT - 0.02, 0.07]} />
          <meshStandardMaterial color="#6b543a" roughness={0.7} />
        </mesh>
        {/* manija */}
        <mesh position={[DOOR_WIDTH - 0.14, DOOR_HEIGHT / 2, 0.06]}>
          <sphereGeometry args={[0.045, 12, 12]} />
          <meshStandardMaterial color="#c9b037" metalness={1} roughness={0.3} />
        </mesh>
      </group>
    </group>
  )
}
