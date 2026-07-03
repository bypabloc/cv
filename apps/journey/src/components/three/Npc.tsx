/**
 * @component Npc
 * @description Humanoide low-poly PROCEDURAL (primitivas, cero .glb) con
 *   animacion por codigo: idle (respiracion + sway) o walk (ciclo de
 *   piernas/brazos + desplazamiento por waypoints en loop).
 *
 *   ponytail: v1 procedural — swap a .glb CC0 (Quaternius/Mixamo) si se
 *   quiere mas fidelidad organica; el contrato (position/path) no cambia.
 */
import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import type { Group } from 'three'

export interface NpcProps {
  /** Posicion base (idle) o punto de arranque (walk). */
  position: [number, number, number]
  /** Waypoints XZ: con 2+ puntos el NPC camina el loop; sin path, idle. */
  path?: readonly [number, number][]
  shirt?: string
  pants?: string
  skin?: string
  /** Casco de seguridad (rubro industrial). */
  helmet?: string
  speed?: number
  rotationY?: number
}

const LIMB_SWING = 0.6

interface LimbRefs {
  leftLeg: Group | null
  rightLeg: Group | null
  leftArm: Group | null
  rightArm: Group | null
}

function setLimbX(limb: Group | null, value: number): void {
  if (limb) {
    limb.rotation.x = value
  }
}

/** Avanza por los waypoints en loop a velocidad constante y orienta el NPC. */
function moveAlongPath(
  root: Group,
  points: readonly [number, number][],
  t: number,
  speed: number,
): void {
  let total = 0
  const lengths: number[] = []
  for (let i = 0; i < points.length; i += 1) {
    const a = points[i]
    const b = points[(i + 1) % points.length]
    const len = a && b ? Math.hypot(b[0] - a[0], b[1] - a[1]) : 0
    lengths.push(len)
    total += len
  }
  if (total === 0) {
    return
  }
  let dist = (t * speed) % total
  let segment = 0
  while (segment < lengths.length && dist > (lengths[segment] ?? 0)) {
    dist -= lengths[segment] ?? 0
    segment += 1
  }
  const a = points[segment % points.length]
  const b = points[(segment + 1) % points.length]
  const len = lengths[segment % lengths.length] ?? 1
  if (!a || !b) {
    return
  }
  const k = len > 0 ? dist / len : 0
  root.position.x = a[0] + (b[0] - a[0]) * k
  root.position.z = a[1] + (b[1] - a[1]) * k
  root.rotation.y = Math.atan2(b[0] - a[0], b[1] - a[1])
}

function applyWalkPose(root: Group, limbs: LimbRefs, t: number): void {
  const swing = Math.sin(t * 5)
  setLimbX(limbs.leftLeg, swing * LIMB_SWING)
  setLimbX(limbs.rightLeg, -swing * LIMB_SWING)
  setLimbX(limbs.leftArm, -swing * LIMB_SWING * 0.8)
  setLimbX(limbs.rightArm, swing * LIMB_SWING * 0.8)
  root.position.y = Math.abs(swing) * 0.03
}

function applyIdlePose(
  root: Group,
  limbs: LimbRefs,
  t: number,
  rotationY: number,
): void {
  root.position.y = Math.sin(t * 1.6) * 0.015
  root.rotation.y = rotationY + Math.sin(t * 0.7) * 0.08
  setLimbX(limbs.leftArm, Math.sin(t * 1.6) * 0.06)
  setLimbX(limbs.rightArm, -Math.sin(t * 1.6) * 0.06)
}

export function Npc({
  position,
  path,
  shirt = '#5a7a9a',
  pants = '#3a4048',
  skin = '#d9a684',
  helmet,
  speed = 0.8,
  rotationY = 0,
}: NpcProps) {
  const rootRef = useRef<Group>(null)
  const leftLegRef = useRef<Group>(null)
  const rightLegRef = useRef<Group>(null)
  const leftArmRef = useRef<Group>(null)
  const rightArmRef = useRef<Group>(null)
  // fase aleatoria estable por instancia (evita NPCs sincronizados)
  const phase = useMemo(
    () => (position[0] * 7.3 + position[2] * 3.1) % (Math.PI * 2),
    [position],
  )
  const walking = (path?.length ?? 0) >= 2

  useFrame(({ clock }) => {
    const root = rootRef.current
    if (!root) {
      return
    }
    const t = clock.elapsedTime + phase
    const limbs: LimbRefs = {
      leftLeg: leftLegRef.current,
      rightLeg: rightLegRef.current,
      leftArm: leftArmRef.current,
      rightArm: rightArmRef.current,
    }
    if (walking && path) {
      moveAlongPath(root, path, t, speed)
      applyWalkPose(root, limbs, t)
    } else {
      applyIdlePose(root, limbs, t, rotationY)
    }
  })

  return (
    <group ref={rootRef} position={position} rotation-y={rotationY}>
      {/* piernas (pivote en cadera y=0.78) */}
      <group ref={leftLegRef} position={[-0.09, 0.78, 0]}>
        <mesh position={[0, -0.39, 0]}>
          <boxGeometry args={[0.13, 0.78, 0.16]} />
          <meshStandardMaterial color={pants} roughness={0.9} />
        </mesh>
      </group>
      <group ref={rightLegRef} position={[0.09, 0.78, 0]}>
        <mesh position={[0, -0.39, 0]}>
          <boxGeometry args={[0.13, 0.78, 0.16]} />
          <meshStandardMaterial color={pants} roughness={0.9} />
        </mesh>
      </group>
      {/* torso */}
      <mesh position={[0, 1.08, 0]}>
        <boxGeometry args={[0.4, 0.6, 0.22]} />
        <meshStandardMaterial color={shirt} roughness={0.85} />
      </mesh>
      {/* brazos (pivote en hombro y=1.32) */}
      <group ref={leftArmRef} position={[-0.26, 1.32, 0]}>
        <mesh position={[0, -0.26, 0]}>
          <boxGeometry args={[0.1, 0.52, 0.12]} />
          <meshStandardMaterial color={shirt} roughness={0.85} />
        </mesh>
      </group>
      <group ref={rightArmRef} position={[0.26, 1.32, 0]}>
        <mesh position={[0, -0.26, 0]}>
          <boxGeometry args={[0.1, 0.52, 0.12]} />
          <meshStandardMaterial color={shirt} roughness={0.85} />
        </mesh>
      </group>
      {/* cabeza */}
      <mesh position={[0, 1.56, 0]}>
        <boxGeometry args={[0.24, 0.26, 0.24]} />
        <meshStandardMaterial color={skin} roughness={0.7} />
      </mesh>
      {helmet && (
        <group position={[0, 1.72, 0]}>
          <mesh>
            <sphereGeometry
              args={[0.16, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2]}
            />
            <meshStandardMaterial color={helmet} roughness={0.5} />
          </mesh>
          <mesh position={[0, 0.001, 0]}>
            <cylinderGeometry args={[0.2, 0.2, 0.02, 12]} />
            <meshStandardMaterial color={helmet} roughness={0.5} />
          </mesh>
        </group>
      )}
    </group>
  )
}
