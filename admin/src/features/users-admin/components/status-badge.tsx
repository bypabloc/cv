'use client'

import { Badge } from '@/components/ui/badge'
import type { UserStatus } from '@/types/models'

/**
 * @component StatusBadge
 * @description Badge de estado del usuario con variant + label en espanol.
 * @props {UserStatus} status - estado del usuario
 */

const STATUS_META: Record<
  UserStatus,
  {
    label: string
    variant: 'default' | 'secondary' | 'destructive' | 'outline'
  }
> = {
  active: { label: 'Activo', variant: 'default' },
  pending: { label: 'Pendiente', variant: 'secondary' },
  disabled: { label: 'Deshabilitado', variant: 'destructive' },
  locked: { label: 'Bloqueado', variant: 'destructive' },
  deleted: { label: 'Eliminado', variant: 'outline' },
}

export function StatusBadge({ status }: { status: UserStatus }) {
  const meta = STATUS_META[status]
  return <Badge variant={meta.variant}>{meta.label}</Badge>
}
