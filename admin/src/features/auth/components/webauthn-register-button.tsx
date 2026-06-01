'use client'

import { startRegistration } from '@simplewebauthn/browser'
import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useWebauthnRegisterOptions } from '../hooks/use-webauthn-register-options'
import { useWebauthnRegisterVerify } from '../hooks/use-webauthn-register-verify'

/**
 * @component WebAuthnRegisterButton
 * @description Registra un passkey: register-options ->
 *   `startRegistration(options)` -> register-verify
 *   (`{challenge_id, response, nickname}`). Requiere sesion activa.
 */
export function WebAuthnRegisterButton() {
  const [nickname, setNickname] = useState('')
  const registerOptions = useWebauthnRegisterOptions()
  const registerVerify = useWebauthnRegisterVerify()
  const isPending = registerOptions.isPending || registerVerify.isPending

  const onRegister = async () => {
    try {
      const { data } = await registerOptions.mutateAsync()
      const response = await startRegistration({ optionsJSON: data.options })
      registerVerify.mutate({
        challenge_id: data.challenge_id,
        response,
        nickname: nickname || undefined,
      })
    } catch {
      toast.error('No pudimos registrar el passkey')
    }
  }

  return (
    <div className="space-y-2">
      <Label htmlFor="passkey-nickname">Nombre del passkey (opcional)</Label>
      <Input
        id="passkey-nickname"
        value={nickname}
        onChange={(event) => setNickname(event.target.value)}
        placeholder="Mi YubiKey"
      />
      <Button
        type="button"
        className="w-full"
        disabled={isPending}
        onClick={() => {
          void onRegister()
        }}
      >
        {isPending ? 'Registrando...' : 'Agregar passkey'}
      </Button>
    </div>
  )
}
