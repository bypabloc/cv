/**
 * @component GuidedTour
 * @description Tier Reduced (movil): la camara recorre el riel del tour
 *   sola (sin joystick), pausando en cada sala mientras el HUD muestra los
 *   textos de la etapa. El menu de teletransporte salta el riel a la sala
 *   elegida. Abre todas las puertas al montar (el riel las cruza).
 */
import { useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import { EYE_HEIGHT, type JourneyLayout, zoneAt } from '../../lib/layout'
import { useJourneyStore } from '../../lib/store'
import { buildTourTimeline, tourPoseAt, tourTimeForRoom } from '../../lib/tour'

interface GuidedTourProps {
  layout: JourneyLayout
}

export function GuidedTour({ layout }: GuidedTourProps) {
  const camera = useThree((state) => state.camera)
  const timeline = useMemo(() => buildTourTimeline(layout), [layout])
  const offsetRef = useRef(0)

  useEffect(() => {
    const store = useJourneyStore.getState()
    for (const door of layout.doors) {
      store.openDoor(door.corridorIndex)
    }
  }, [layout])

  useFrame(({ clock }, dt) => {
    const store = useJourneyStore.getState()
    const teleport = store.consumeTeleport()
    if (teleport) {
      const zone = zoneAt(layout, teleport.z)
      offsetRef.current =
        tourTimeForRoom(timeline, zone.index) - clock.elapsedTime
    }
    if (store.isUiOpen()) {
      // congela el riel mientras un panel esta abierto
      offsetRef.current -= dt
      return
    }
    const pose = tourPoseAt(timeline, clock.elapsedTime + offsetRef.current)
    camera.position.set(pose.x, EYE_HEIGHT, pose.z)
    camera.lookAt(pose.lookX, EYE_HEIGHT, pose.lookZ)
    const zone = zoneAt(layout, pose.z)
    if (zone.kind !== store.zone.kind || zone.index !== store.zone.index) {
      store.setZone(zone)
    }
  })

  return null
}
