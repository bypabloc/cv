'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { ErrorAlert } from '@/components/ui/error-alert'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDate } from '@/lib/format/date'
import { ROUTES } from '@/lib/routes'
import { useUserDetail } from '../hooks/use-user-detail'
import { StatusBadge } from './status-badge'
import { UserActionsMenu } from './user-actions-menu'

/**
 * @component UserDetailDrawer
 * @description Sheet lateral con el detalle de un usuario. El id se lee del
 *   deep-link `?user=<id>` via `useSearchParams` (NO ruta dinamica, consistente
 *   con `output: 'export'`). Debe renderizarse DENTRO de un `<Suspense>`. Cerrar
 *   el Sheet limpia el query param navegando a `/users`.
 */
export function UserDetailDrawer() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const userId = searchParams.get('user')
  const { data: user, isLoading, error, refetch } = useUserDetail(userId)

  const handleOpenChange = (open: boolean) => {
    if (!open) router.replace(ROUTES.admin.users)
  }

  return (
    <Sheet open={Boolean(userId)} onOpenChange={handleOpenChange}>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Detalle del usuario</SheetTitle>
          <SheetDescription>
            Informacion y acciones del usuario seleccionado.
          </SheetDescription>
        </SheetHeader>

        <div className="flex flex-col gap-4 p-4">
          {isLoading ? (
            <div className="space-y-3">
              <LoadingSpinner />
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-5 w-1/2" />
            </div>
          ) : null}

          {error ? (
            <ErrorAlert error={error} onRetry={() => refetch()} />
          ) : null}

          {user ? (
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-muted-foreground">Email</dt>
                <dd className="font-medium">{user.email}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Nombre</dt>
                <dd className="font-medium">{user.display_name ?? '-'}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Estado</dt>
                <dd>
                  <StatusBadge status={user.status} />
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Metodos MFA</dt>
                <dd className="font-medium">{user.total_mfa}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Creado</dt>
                <dd className="font-medium">{formatDate(user.created_at)}</dd>
              </div>
              <div className="pt-2">
                <UserActionsMenu user={user} />
              </div>
            </dl>
          ) : null}
        </div>
      </SheetContent>
    </Sheet>
  )
}
