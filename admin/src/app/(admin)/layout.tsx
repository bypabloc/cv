'use client'

import type { ReactNode } from 'react'
import { Header } from '@/features/admin-shell/components/header'
import { Sidebar } from '@/features/admin-shell/components/sidebar'
import { AuthGuard } from '@/features/auth/components/auth-guard'

/**
 * @page AdminLayout
 * @description Layout protegido del area autenticada (route group `(admin)`).
 *   AuthGuard redirige a /login si no hay sesion; el shell (Sidebar + Header)
 *   persiste entre navegaciones del grupo (no se remonta).
 */
export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex flex-1 flex-col">
          <Header />
          <main className="flex-1 overflow-auto p-6">{children}</main>
        </div>
      </div>
    </AuthGuard>
  )
}
