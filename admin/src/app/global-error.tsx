'use client'

/**
 * @page GlobalError
 * @description Fallback ultimo (error en el propio RootLayout). Debe
 *   renderizar su propio <html>/<body>.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html lang="es">
      <body>
        <div
          style={{
            display: 'flex',
            minHeight: '100vh',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '1rem',
            padding: '1.5rem',
          }}
        >
          <h1>Error critico</h1>
          <p>{error.message}</p>
          <button type="button" onClick={reset}>
            Reintentar
          </button>
        </div>
      </body>
    </html>
  )
}
