/**
 * @component JourneyApp
 * @description Composicion de la experiencia 3D: Canvas R3F (tone mapping
 *   ACES, DPR por tier) + estructura procedural + salas lazy + puertas +
 *   controles + HUD. El portal al pasado aplica sepia + grano via CSS
 *   filter sobre el canvas (barato, sin post-processing).
 *   Se carga por dynamic import desde la isla (chunk separado del CV).
 */
import { Canvas, useThree } from '@react-three/fiber'
import { useEffect, useMemo } from 'react'
import { AgXToneMapping, PMREMGenerator } from 'three'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'
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
import { GuidedTour } from './GuidedTour'
import { Hud } from './Hud'
import { PlayerControls } from './PlayerControls'
import { RoomContents } from './RoomContents'
import { ShadowGroup } from './ShadowGroup'
import { Structure } from './Structure'

/**
 * IBL procedural self-hosted: RoomEnvironment (viene dentro de three, cero
 * CDN — el preset de drei Environment descarga HDRIs de raw.githack y la
 * CSP lo prohibe) via PMREM como scene.environment. Es lo que hace que
 * MeshStandardMaterial tenga algo que reflejar y no se vea "plastico".
 */
function ProceduralEnvironment({ intensity }: { intensity: number }) {
  const gl = useThree((s) => s.gl)
  const scene = useThree((s) => s.scene)
  useEffect(() => {
    const pmrem = new PMREMGenerator(gl)
    const roomEnv = new RoomEnvironment()
    const target = pmrem.fromScene(roomEnv, 0.04)
    scene.environment = target.texture
    scene.environmentIntensity = intensity
    return () => {
      scene.environment = null
      target.dispose()
      pmrem.dispose()
    }
  }, [gl, scene, intensity])
  return null
}

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
          shadows={tier === 'full' ? 'soft' : false}
          dpr={tier === 'full' ? [1, 2] : [1, 1.5]}
          gl={{ antialias: true, powerPreference: 'high-performance' }}
          camera={{
            fov: 72,
            near: 0.05,
            far: 140,
            position: [0, EYE_HEIGHT, startZ],
          }}
          onCreated={({ gl, camera }) => {
            // AgX (r160+) sobre el ACES default de R3F: ACES oscurece y
            // desatura interiores; AgX + exposure ~1.15 da el look natural
            gl.toneMapping = AgXToneMapping
            gl.toneMappingExposure = 1.15
            camera.lookAt(0, EYE_HEIGHT, startZ + 5)
          }}
        >
          <color attach="background" args={['#07070b']} />
          <fog attach="fog" args={['#07070b', 12, 70]} />
          <ProceduralEnvironment intensity={0.6} />
          {/* fill bajo: el relleno real lo da el environment (IBL) */}
          <hemisphereLight args={['#94a7c8', '#2a2622', 0.3]} />
          <Structure layout={layout} rooms={rooms} walls={walls} />
          <RoomContents
            rooms={rooms}
            layout={layout}
            pastRooms={pastRooms}
            pastWalls={pastWalls}
          />
          <ShadowGroup>
            {layout.doors.map((door) => (
              <Door key={door.corridorIndex} door={door} />
            ))}
          </ShadowGroup>
          {tier === 'reduced' ? (
            <GuidedTour layout={layout} />
          ) : (
            <PlayerControls layout={layout} walls={colliders} />
          )}
        </Canvas>
      </div>
      {/* vignette CSS: sensacion de lente sin lib de post-processing */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          background:
            'radial-gradient(ellipse at center, transparent 58%, rgba(0,0,0,0.4) 100%)',
        }}
      />
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
