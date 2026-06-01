'use client'

import Link from 'next/link'
import { LoginForm } from '@/features/auth/components/login-form'
import { ROUTES } from '@/lib/routes'

/**
 * @page LoginPage
 * @description Pagina de inicio de sesion (ruta `/login`).
 */
export default function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6">
      <div className="w-full max-w-sm space-y-6">
        <h1 className="text-2xl font-bold">Iniciar sesion</h1>
        <LoginForm />
        <p className="text-center text-sm text-muted-foreground">
          No tenes cuenta?{' '}
          <Link
            href={ROUTES.auth.register}
            className="text-primary hover:underline"
          >
            Registrate
          </Link>
        </p>
      </div>
    </div>
  )
}
