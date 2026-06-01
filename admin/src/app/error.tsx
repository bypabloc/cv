'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

/**
 * @page ErrorBoundary
 * @description Error boundary global del App Router.
 */
export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // biome-ignore lint/suspicious/noConsole: error boundary logging
    console.error(error)
  }, [error])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
      <h1 className="text-xl font-semibold">Algo salio mal</h1>
      <p className="text-sm text-muted-foreground">{error.message}</p>
      <Button onClick={reset}>Reintentar</Button>
    </div>
  )
}
