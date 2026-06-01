'use client'

import { useMutation } from '@tanstack/react-query'
import { authClient } from '../api/auth-client'

/**
 * @function useGenerateRecoveryCodes
 * @description Genera 10 recovery codes (mostrados UNA sola vez). El caller
 *   debe forzar al usuario a guardarlos antes de cerrar el modal.
 */
export function useGenerateRecoveryCodes() {
  return useMutation({
    mutationFn: authClient.mfaRecoveryCodesGenerate,
  })
}
