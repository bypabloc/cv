'use client'

import { useMutation } from '@tanstack/react-query'
import { authClient } from '../api/auth-client'

/**
 * @function useWebauthnLoginOptions
 * @description Pide las options para el login passwordless con passkey (sin
 *   sesion previa). El caller las pasa a `startAuthentication`.
 */
export function useWebauthnLoginOptions() {
  return useMutation({
    mutationFn: authClient.webauthnLoginOptions,
  })
}
