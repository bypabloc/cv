/**
 * @component JourneyApp
 * @description Composicion de la experiencia 3D: Canvas R3F (tone mapping
 *   ACES, DPR por tier) + estructura procedural + puertas + controles +
 *   HUD. Se carga por dynamic import desde la isla (chunk separado del CV).
 */
import { Canvas } from '@react-three/fiber'
import { useEffect, useMemo } from 'react'
import { ACESFilmicToneMapping } from 'three'
import { buildLayout, buildWallBoxes, EYE_HEIGHT } from '../../lib/layout'
import { buildRooms, type Locale } from '../../lib/rooms'
import { useJourneyStore } from '../../lib/store'
import type { Tier } from '../../lib/tiers'
import { Door } from './Door'
import { Hud } from './Hud'
import { PlayerControls } from './PlayerControls'
import { Structure } from './Structure'

interface JourneyAppProps {
  tier: Exclude<Tier, 'static'>
  locale: Locale
  onExit: () => void
}

export default function JourneyApp({ tier, locale, onExit }: JourneyAppProps) {
  const rooms = useMemo(() => buildRooms(), [])
  const layout = useMemo(() => buildLayout(rooms), [rooms])
  const walls = useMemo(() => buildWallBoxes(layout), [layout])

  useEffect(() => {
    useJourneyStore.getState().configure(tier, locale)
  }, [tier, locale])

  const firstRoom = layout.rooms[0]
  const startZ = firstRoom ? firstRoom.z - firstRoom.depth / 4 : 2

  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      <Canvas
        shadows={tier === 'full'}
        dpr={tier === 'full' ? [1, 2] : [1, 1.5]}
        camera={{
          fov: 72,
          near: 0.05,
          far: 140,
          position: [0, EYE_HEIGHT, startZ],
        }}
        onCreated={({ gl, camera }) => {
          gl.toneMapping = ACESFilmicToneMapping
          camera.lookAt(0, EYE_HEIGHT, startZ + 5)
        }}
      >
        <color attach="background" args={['#07070b']} />
        <fog attach="fog" args={['#07070b', 12, 70]} />
        <hemisphereLight args={['#94a7c8', '#2a2622', 0.45]} />
        <Structure layout={layout} rooms={rooms} walls={walls} />
        {layout.doors.map((door) => (
          <Door key={door.corridorIndex} door={door} />
        ))}
        <PlayerControls layout={layout} walls={walls} />
      </Canvas>
      <Hud rooms={rooms} locale={locale} onExit={onExit} />
    </div>
  )
}
