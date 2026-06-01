'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { useAuthStore } from '@/features/auth/store/use-auth-store'
import { ROUTES } from '@/lib/routes'

/**
 * @page HomePage
 * @description Landing del area protegida (`/`). Si no hay sesion, redirige a
 *   /login; el AuthGuard del (admin)/layout ya cubre esto, pero la page raiz
 *   muestra un placeholder de bienvenida mientras resuelve.
 */
export default function HomePage() {
  const router = useRouter()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace(ROUTES.auth.login)
    }
  }, [isAuthenticated, router])

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">Cargando...</p>
    </div>
  )
}
