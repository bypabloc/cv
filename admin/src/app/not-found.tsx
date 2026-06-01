import Link from 'next/link'
import { Button } from '@/components/ui/button'

/**
 * @page NotFound
 * @description Pagina 404 del admin.
 */
export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
      <h1 className="text-2xl font-bold">404</h1>
      <p className="text-sm text-muted-foreground">Pagina no encontrada</p>
      <Button asChild>
        <Link href="/">Volver al inicio</Link>
      </Button>
    </div>
  )
}
