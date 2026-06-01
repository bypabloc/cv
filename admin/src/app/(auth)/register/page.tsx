'use client'

import Link from 'next/link'
import { RegisterForm } from '@/features/auth/components/register-form'
import { ROUTES } from '@/lib/routes'

/**
 * @page RegisterPage
 * @description Pagina de registro (ruta `/register`).
 */
export default function RegisterPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6">
      <div className="w-full max-w-sm space-y-6">
        <h1 className="text-2xl font-bold">Crear cuenta</h1>
        <RegisterForm />
        <p className="text-center text-sm text-muted-foreground">
          Ya tenes cuenta?{' '}
          <Link
            href={ROUTES.auth.login}
            className="text-primary hover:underline"
          >
            Inicia sesion
          </Link>
        </p>
      </div>
    </div>
  )
}
