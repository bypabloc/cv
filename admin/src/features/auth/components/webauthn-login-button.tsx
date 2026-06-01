'use client'

import { startAuthentication } from '@simplewebauthn/browser'
import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useWebauthnLoginOptions } from '../hooks/use-webauthn-login-options'
import { useWebauthnLoginVerify } from '../hooks/use-webauthn-login-verify'

/**
 * @component WebAuthnLoginButton
 * @description Login passwordless con passkey: pide email -> login-options ->
 *   `startAuthentication(options)` -> login-verify (`{challenge_id, response}`).
 *   No requiere sesion previa.
 */
export function WebAuthnLoginButton() {
  const [email, setEmail] = useState('')
  const loginOptions = useWebauthnLoginOptions()
  const loginVerify = useWebauthnLoginVerify()
  const isPending = loginOptions.isPending || loginVerify.isPending

  const onUsePasskey = async () => {
    if (!email) {
      toast.error('Ingresa tu email')
      return
    }
    try {
      const { data } = await loginOptions.mutateAsync({ email })
      const response = await startAuthentication({ optionsJSON: data.options })
      loginVerify.mutate({ challenge_id: data.challenge_id, response })
    } catch {
      toast.error('No pudimos iniciar el login con passkey')
    }
  }

  return (
    <div className="space-y-2">
      <Label htmlFor="webauthn-email">Email (para passkey)</Label>
      <Input
        id="webauthn-email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />
      <Button
        type="button"
        variant="outline"
        className="w-full"
        disabled={isPending}
        onClick={() => {
          void onUsePasskey()
        }}
      >
        {isPending ? 'Validando...' : 'Usar passkey'}
      </Button>
    </div>
  )
}
