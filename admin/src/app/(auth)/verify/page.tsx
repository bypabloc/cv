'use client'

import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MagicLinkPrompt } from '@/features/auth/components/magic-link-prompt'
import { VerifyCodeInput } from '@/features/auth/components/verify-code-input'

/**
 * @component VerifyContent
 * @description Contenido de la pagina verify. Lee `?flow=` para decidir si la
 *   verificacion es de register o login.
 */
function VerifyContent() {
  const params = useSearchParams()
  const flow = params.get('flow') === 'login' ? 'login' : 'register'

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6">
      <div className="w-full max-w-sm space-y-6">
        <h1 className="text-2xl font-bold">Verifica tu email</h1>
        <Tabs defaultValue="code">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="code">Codigo</TabsTrigger>
            <TabsTrigger value="magic-link">Magic link</TabsTrigger>
          </TabsList>
          <TabsContent value="code">
            <VerifyCodeInput flow={flow} />
          </TabsContent>
          <TabsContent value="magic-link">
            <MagicLinkPrompt />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

/**
 * @page VerifyPage
 * @description Pagina de verificacion de email (ruta `/verify`). Suspense
 *   obligatorio porque `useSearchParams` lo requiere en export mode.
 */
export default function VerifyPage() {
  return (
    <Suspense fallback={<div className="p-6">Cargando...</div>}>
      <VerifyContent />
    </Suspense>
  )
}
