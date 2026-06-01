import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, userEvent, waitFor } from '@tests/utils/render'
import type { ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { UserActionsMenu } from '@/features/users-admin/components/user-actions-menu'
import type { AdminUser } from '@/types/models'

/**
 * @module tests/unit/features/users-admin/user-actions-menu
 * @description Verifica que el menu muestra Deshabilitar para un user activo y
 *   que la accion invalida las queries `admin` en exito.
 */

const ACTIVE_USER: AdminUser = {
  user_id: 'usr_01',
  email: 'user@test.com',
  display_name: 'Pablo',
  status: 'active',
  created_at: '2026-01-01T00:00:00Z',
  total_mfa: 2,
}

const DISABLED_USER: AdminUser = {
  ...ACTIVE_USER,
  user_id: 'usr_02',
  email: 'other@test.com',
  status: 'disabled',
}

function renderWithSpy(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const invalidateSpy = vi.spyOn(client, 'invalidateQueries')
  const result = render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  )
  return { ...result, invalidateSpy }
}

describe('UserActionsMenu', () => {
  it('Given un user activo When abrir el menu y clic en Deshabilitar Then invalida las queries admin', async () => {
    // Arrange
    const { invalidateSpy } = renderWithSpy(
      <UserActionsMenu user={ACTIVE_USER} />,
    )

    // Act
    await userEvent.click(screen.getByRole('button', { name: /acciones/i }))
    await userEvent.click(
      await screen.findByRole('menuitem', { name: /deshabilitar/i }),
    )

    // Assert
    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: ['admin', 'users'],
      })
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['admin', 'user', 'usr_01'],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['admin', 'actions'],
    })
  })

  it('Given un user deshabilitado When abrir el menu y clic en Habilitar Then invalida las queries admin', async () => {
    // Arrange
    const { invalidateSpy } = renderWithSpy(
      <UserActionsMenu user={DISABLED_USER} />,
    )

    // Act
    await userEvent.click(screen.getByRole('button', { name: /acciones/i }))
    const enableItem = await screen.findByRole('menuitem', {
      name: /habilitar/i,
    })

    // Assert: el menu muestra Habilitar, no Deshabilitar
    expect(
      screen.queryByRole('menuitem', { name: /deshabilitar/i }),
    ).not.toBeInTheDocument()

    await userEvent.click(enableItem)
    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: ['admin', 'user', 'usr_02'],
      })
    })
  })

  it('Given un user When clic en Forzar logout Then invalida las queries admin', async () => {
    // Arrange
    const { invalidateSpy } = renderWithSpy(
      <UserActionsMenu user={ACTIVE_USER} />,
    )

    // Act
    await userEvent.click(screen.getByRole('button', { name: /acciones/i }))
    await userEvent.click(
      await screen.findByRole('menuitem', { name: /forzar logout/i }),
    )

    // Assert
    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: ['admin', 'user', 'usr_01'],
      })
    })
  })

  it('Given clic en Eliminar When confirmar el AlertDialog Then invalida las queries admin', async () => {
    // Arrange
    const { invalidateSpy } = renderWithSpy(
      <UserActionsMenu user={ACTIVE_USER} />,
    )

    // Act: abrir menu -> Eliminar -> confirmar en el AlertDialog
    await userEvent.click(screen.getByRole('button', { name: /acciones/i }))
    await userEvent.click(
      await screen.findByRole('menuitem', { name: /eliminar/i }),
    )
    const confirm = await screen.findByRole('button', { name: 'Eliminar' })
    await userEvent.click(confirm)

    // Assert
    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: ['admin', 'user', 'usr_01'],
      })
    })
  })
})
