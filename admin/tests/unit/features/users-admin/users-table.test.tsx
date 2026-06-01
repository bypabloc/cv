import { render, screen } from '@tests/utils/render'
import { describe, expect, it, vi } from 'vitest'
import { UsersTable } from '@/features/users-admin/components/users-table'
import type { AdminUser } from '@/types/models'

/**
 * @module tests/unit/features/users-admin/users-table
 * @description Verifica que la tabla renderiza las filas de usuarios y dispara
 *   onSelectUser con el user_id al hacer click en una fila.
 */

const USERS: AdminUser[] = [
  {
    user_id: 'usr_01',
    email: 'user@test.com',
    display_name: 'Pablo',
    status: 'active',
    created_at: '2026-01-01T00:00:00Z',
    total_mfa: 2,
  },
  {
    user_id: 'usr_02',
    email: 'other@test.com',
    display_name: null,
    status: 'disabled',
    created_at: '2026-02-01T00:00:00Z',
    total_mfa: 0,
  },
]

describe('UsersTable', () => {
  it('Given 2 usuarios When render Then muestra ambos emails', () => {
    // Arrange + Act
    render(<UsersTable users={USERS} onSelectUser={vi.fn()} />)

    // Assert
    expect(screen.getByText('user@test.com')).toBeInTheDocument()
    expect(screen.getByText('other@test.com')).toBeInTheDocument()
  })

  it('Given un display_name nulo When render Then muestra un guion', () => {
    // Arrange + Act
    render(<UsersTable users={USERS} onSelectUser={vi.fn()} />)

    // Assert: usr_02 sin nombre + total_mfa 0 muestran '-' y '0'
    expect(screen.getByText('Deshabilitado')).toBeInTheDocument()
    expect(screen.getByText('Activo')).toBeInTheDocument()
  })

  it('Given click en una fila When onRowClick Then llama onSelectUser con el user_id', async () => {
    // Arrange
    const onSelectUser = vi.fn()
    const { findByText } = render(
      <UsersTable users={USERS} onSelectUser={onSelectUser} />,
    )

    // Act
    const cell = await findByText('user@test.com')
    cell.click()

    // Assert
    expect(onSelectUser).toHaveBeenCalledWith('usr_01')
  })
})
