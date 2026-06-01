'use client'

import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { authClient } from '../api/auth-client'

/**
 * @function useResendCode
 * @description Reenvia el code de verificacion (verify.resend-code). El
 *   backend tiene su propio rate-limit (1/60s, 3/5min).
 */
export function useResendCode() {
  return useMutation({
    mutationFn: authClient.resendCode,
    onSuccess: () => {
      toast.success('Reenviamos el email')
    },
    onError: (error) => {
      toast.error(error.message)
    },
  })
}
