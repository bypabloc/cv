/**
 * @component ShadowGroup
 * @description Marca cast/receiveShadow en todos los meshes hijos via
 *   traverse (los props de sala son primitivas estaticas: repetir castShadow
 *   en cada mesh seria churn). Inofensivo en tiers sin sombras (el shadowMap
 *   del renderer esta apagado). El effect corre sin deps para alcanzar
 *   tambien a los hijos lazy que montan tarde (Suspense, drei Text).
 */
import { type ReactNode, useEffect, useRef } from 'react'
import { type Group, Mesh } from 'three'

export function ShadowGroup({ children }: { children: ReactNode }) {
  const ref = useRef<Group>(null)
  useEffect(() => {
    ref.current?.traverse((obj) => {
      if (obj instanceof Mesh) {
        obj.castShadow = true
        obj.receiveShadow = true
      }
    })
  })
  return <group ref={ref}>{children}</group>
}
