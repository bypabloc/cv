/**
 * @component JourneyApp
 * @description Composicion de la experiencia 3D: Canvas R3F (tone mapping
 *   ACES, DPR por tier) + estructura procedural + salas lazy + puertas +
 *   controles + HUD. El portal al pasado aplica sepia + grano via CSS
 *   filter sobre el canvas (barato, sin post-processing).
 *   Se carga por dynamic import desde la isla (chunk separado del CV).
 */
import { Canvas } from '@react-three/fiber'
import { useEffect, useMemo } from 'react'
import { ACESFilmicToneMapping } from 'three'
import {
  buildLayout,
  buildPastRooms,
  buildPastWallBoxes,
  buildWallBoxes,
  EYE_HEIGHT,
} from '../../lib/layout'
import { buildRooms, type Locale } from '../../lib/rooms'
import { useJourneyStore } from '../../lib/store'
import type { Tier } from '../../lib/tiers'
import { ambientAudio } from './ambient-audio'
import { Door } from './Door'
import { Hud } from './Hud'
import { PlayerControls } from './PlayerControls'
import { RoomContents } from './RoomContents'
import { Structure } from './Structure'

interface JourneyAppProps {
  tier: Exclude<Tier, 'static'>
  locale: Locale
  onExit: () => void
}

const GRAIN_KEYFRAMES = `
@keyframes journey-glitch-in {
  0% { opacity: 1; transform: translateX(0); }
  20% { opacity: 0.6; transform: translateX(-6px); }
  40% { opacity: 0.9; transform: translateX(5px); }
  60% { opacity: 0.5; transform: translateX(-3px); }
  100% { opacity: 0; transform: translateX(0); }
}
@keyframes journey-grain {
  0% { background-position: 0 0; }
  100% { background-position: 90px 60px; }
}
`

export default function JourneyApp({ tier, locale, onExit }: JourneyAppProps) {
  const rooms = useMemo(() => buildRooms(), [])
  const layout = useMemo(() => buildLayout(rooms), [rooms])
  const walls = useMemo(() => buildWallBoxes(layout), [layout])
  const pastRooms = useMemo(() => buildPastRooms(layout), [layout])
  const pastWalls = useMemo(() => buildPastWallBoxes(pastRooms), [pastRooms])
  const colliders = useMemo(() => [...walls, ...pastWalls], [walls, pastWalls])
  const inPast = useJourneyStore((s) => s.past !== null)
  const audioOn = useJourneyStore((s) => s.audioOn)
  const zone = useJourneyStore((s) => s.zone)
  const audioRoomId =
    rooms[zone.kind === 'corridor' ? zone.index + 1 : zone.index]?.id ?? 'aula'

  useEffect(() => {
    useJourneyStore.getState().configure(tier, locale)
  }, [tier, locale])

  // audio ambiente por sala — SIEMPRE opt-in (toggle del HUD)
  useEffect(() => {
    if (audioOn) {
      ambientAudio.enable(audioRoomId)
    } else {
      ambientAudio.disable()
    }
  }, [audioOn, audioRoomId])
  useEffect(() => () => ambientAudio.disable(), [])

  const firstRoom = layout.rooms[0]
  const startZ = firstRoom ? firstRoom.z - firstRoom.depth / 4 : 2

  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      <style>{GRAIN_KEYFRAMES}</style>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          // estetica retro del pasado: sepia + desaturado (plan, mejora 2)
          filter: inPast
            ? 'sepia(0.72) saturate(0.55) contrast(1.06) brightness(0.92)'
            : 'none',
          transition: 'filter 400ms ease',
        }}
      >
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
          <RoomContents
            rooms={rooms}
            layout={layout}
            pastRooms={pastRooms}
            pastWalls={pastWalls}
          />
          {layout.doors.map((door) => (
            <Door key={door.corridorIndex} door={door} />
          ))}
          <PlayerControls layout={layout} walls={colliders} />
        </Canvas>
      </div>
      {/* grano + glitch de transicion al cruzar el portal */}
      {inPast && (
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            inset: 0,
            pointerEvents: 'none',
            opacity: 0.16,
            backgroundImage:
              'radial-gradient(circle, rgba(255,255,255,0.35) 1px, transparent 1px)',
            backgroundSize: '3px 3px',
            animation: 'journey-grain 0.7s steps(4) infinite',
            mixBlendMode: 'overlay',
          }}
        />
      )}
      {inPast && (
        <div
          key="glitch"
          aria-hidden="true"
          style={{
            position: 'absolute',
            inset: 0,
            pointerEvents: 'none',
            background: '#d8c8a8',
            animation: 'journey-glitch-in 450ms steps(5) forwards',
          }}
        />
      )}
      <Hud rooms={rooms} layout={layout} locale={locale} onExit={onExit} />
    </div>
  )
}
