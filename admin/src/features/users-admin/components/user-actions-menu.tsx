'use client'

import { LogOut, MoreHorizontal, Trash2, UserCheck, UserX } from 'lucide-react'
import { useState } from 'react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { AdminUser } from '@/types/models'
import { useDeleteUser } from '../hooks/use-delete-user'
import { useDisableUser } from '../hooks/use-disable-user'
import { useEnableUser } from '../hooks/use-enable-user'
import { useForceLogout } from '../hooks/use-force-logout'

/**
 * @component UserActionsMenu
 * @description Dropdown de acciones sobre un usuario: Deshabilitar / Habilitar
 *   (segun `status`), Forzar logout, y Eliminar (con AlertDialog de
 *   confirmacion). Cada accion invoca su mutation; las queries se invalidan en
 *   exito desde el hook.
 * @props {AdminUser} user - usuario objetivo de las acciones
 */
export function UserActionsMenu({ user }: { user: AdminUser }) {
  const [deleteOpen, setDeleteOpen] = useState(false)
  const disableUser = useDisableUser()
  const enableUser = useEnableUser()
  const deleteUser = useDeleteUser()
  const forceLogout = useForceLogout()

  const isDisabled = user.status === 'disabled'

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Acciones"
            onClick={(event) => event.stopPropagation()}
          >
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {isDisabled ? (
            <DropdownMenuItem
              onSelect={() => enableUser.mutate({ user_id: user.user_id })}
            >
              <UserCheck className="h-4 w-4" />
              Habilitar
            </DropdownMenuItem>
          ) : (
            <DropdownMenuItem
              onSelect={() => disableUser.mutate({ user_id: user.user_id })}
            >
              <UserX className="h-4 w-4" />
              Deshabilitar
            </DropdownMenuItem>
          )}
          <DropdownMenuItem
            onSelect={() => forceLogout.mutate({ user_id: user.user_id })}
          >
            <LogOut className="h-4 w-4" />
            Forzar logout
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            variant="destructive"
            onSelect={() => setDeleteOpen(true)}
          >
            <Trash2 className="h-4 w-4" />
            Eliminar
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminar usuario</AlertDialogTitle>
            <AlertDialogDescription>
              Esta accion eliminara la cuenta de {user.email}. No se puede
              deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={() => deleteUser.mutate({ user_id: user.user_id })}
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
