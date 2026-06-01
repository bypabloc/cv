'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { ApiError } from '@/lib/api-client'
import { useRevokeSession } from '../hooks/use-revoke-session'

/**
 * @component RevokeSessionButton
 * @description Boton para revocar una sesion de la cuenta. Deshabilitado cuando
 *   `isCurrent === true` (defensa en profundidad; el backend es la fuente de
 *   verdad y responde 400 CANNOT_REVOKE_CURRENT_SESSION). Ante un 400 muestra
 *   el error inline y NO revoca. En exito el hook invalida la lista.
 *
 * @props {string} sessionId - id de la sesion a revocar
 * @props {boolean} isCurrent - true si es la sesion en curso (boton inhabilitado)
 */
export function RevokeSessionButton({
  sessionId,
  isCurrent,
}: {
  sessionId: string
  isCurrent: boolean
}) {
  const { mutate, isPending } = useRevokeSession()
  const [inlineError, setInlineError] = useState<string | null>(null)

  const handleRevoke = () => {
    setInlineError(null)
    mutate(
      { session_id: sessionId },
      {
        onError: (error) => {
          if (error instanceof ApiError && error.status === 400) {
            setInlineError('No puedes revocar la sesion actual')
            return
          }
          setInlineError(
            error instanceof Error ? error.message : 'Error al revocar',
          )
        },
      },
    )
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <Button
        type="button"
        variant="destructive"
        size="sm"
        disabled={isCurrent || isPending}
        onClick={handleRevoke}
      >
        {isPending ? <LoadingSpinner /> : null}
        Revocar
      </Button>
      {inlineError ? (
        <p className="text-xs text-destructive" role="alert">
          {inlineError}
        </p>
      ) : null}
    </div>
  )
}
