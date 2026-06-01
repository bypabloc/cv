import { AlertCircle } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

/**
 * @component ErrorAlert
 * @description Alert destructive con mensaje + boton de reintento opcional.
 * @props {unknown} error - Error o ApiError (lee .message si existe)
 * @props {() => void} [onRetry] - callback de reintento
 * @props {string} [title] - titulo (default 'Error')
 */
export function ErrorAlert({
  error,
  onRetry,
  title = 'Error',
}: {
  error: unknown
  onRetry?: () => void
  title?: string
}) {
  const message =
    error instanceof Error ? error.message : 'Ocurrio un error inesperado'
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="flex flex-col gap-2">
        <span>{message}</span>
        {onRetry ? (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="w-fit"
          >
            Reintentar
          </Button>
        ) : null}
      </AlertDescription>
    </Alert>
  )
}
