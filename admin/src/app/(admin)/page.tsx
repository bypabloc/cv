'use client'

import { useAuthStore } from '@/features/auth/store/use-auth-store'

/**
 * @page AdminHomePage
 * @description Landing del area protegida (`/`). Las pantallas de metricas las
 *   monta el plan b-analytics-api en /metrics; aqui un saludo + estado.
 */
export default function AdminHomePage() {
  const user = useAuthStore((s) => s.user)
  return (
    <section className="mx-auto max-w-2xl space-y-2">
      <h1 className="text-2xl font-semibold">Panel de administracion</h1>
      <p className="text-sm text-muted-foreground">
        Sesion iniciada{user?.email ? ` como ${user.email}` : ''}. Usa el menu
        lateral para gestionar tu cuenta, tus sesiones y los usuarios.
      </p>
    </section>
  )
}
