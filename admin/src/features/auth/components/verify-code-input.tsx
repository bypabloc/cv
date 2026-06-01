'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from '@/components/ui/input-otp'
import { useLoginVerifyCode } from '../hooks/use-login-verify-code'
import { useRegisterVerifyCode } from '../hooks/use-register-verify-code'
import { useAuthStore } from '../store/use-auth-store'

const CODE_LENGTH = 8
const CROCKFORD = /^[0-9A-HJ-NP-Z]*$/

/**
 * @component VerifyCodeInput
 * @description InputOTP de 8 chars (alfabeto Crockford). Segun `flow` dispara
 *   register.verify-code o login.verify-code con el temp_token del store.
 *
 * @props {'register' | 'login'} flow - De que operacion es la verificacion
 */
export function VerifyCodeInput({ flow }: { flow: 'register' | 'login' }) {
  const [code, setCode] = useState('')
  const tempToken = useAuthStore((s) => s.tempToken)
  const registerVerify = useRegisterVerifyCode()
  const loginVerify = useLoginVerifyCode()

  const verify = flow === 'register' ? registerVerify : loginVerify
  const isPending = verify.isPending

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (code.length !== CODE_LENGTH || !tempToken) return
    verify.mutate({ code, temp_token: tempToken })
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <InputOTP
        maxLength={CODE_LENGTH}
        value={code}
        onChange={(value) => {
          const upper = value.toUpperCase()
          if (CROCKFORD.test(upper)) setCode(upper)
        }}
        aria-label="Codigo de verificacion"
      >
        <InputOTPGroup>
          {Array.from({ length: CODE_LENGTH }, (_, i) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: el slot OTP es posicional y de longitud fija; el index es su identificador canonico
            <InputOTPSlot key={`otp-${flow}-${i}`} index={i} />
          ))}
        </InputOTPGroup>
      </InputOTP>

      <Button
        type="submit"
        className="w-full"
        disabled={isPending || code.length !== CODE_LENGTH || !tempToken}
      >
        {isPending ? 'Verificando...' : 'Verificar'}
      </Button>
    </form>
  )
}
