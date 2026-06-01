import { server } from '@tests/mocks/server'
import { render, screen, userEvent, waitFor } from '@tests/utils/render'
import { HttpResponse, http } from 'msw'
import { describe, expect, it, vi } from 'vitest'
import { UserDetailDrawer } from '@/features/users-admin/components/user-detail-drawer'

/**
 * @module tests/unit/features/users-admin/user-detail-drawer
 * @description Verifica que el drawer lee `?user=<id>` (deep-link), carga el
 *   detalle via admin.get-user (MSW), muestra el error si el usuario no existe
 *   y cierra navegando a /users.
 */

const API = 'https://api.test.the-full-stack.com'

const { state, replaceMock } = vi.hoisted(() => ({
  state: { search: 'user=usr_01' },
  replaceMock: vi.fn(),
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: replaceMock, push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(state.search),
}))

describe('UserDetailDrawer', () => {
  it('Given ?user=usr_01 When render Then carga y muestra el email del usuario', async () => {
    // Arrange
    state.search = 'user=usr_01'

    // Act
    render(<UserDetailDrawer />)

    // Assert
    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument()
    })
  })

  it('Given ?user=missing When get-user 404 Then muestra el ErrorAlert', async () => {
    // Arrange
    state.search = 'user=missing'
    server.use(
      http.post(`${API}/users`, () =>
        HttpResponse.json(
          { error: 'NOT_FOUND', code: 4040, message: 'No encontrado' },
          { status: 404 },
        ),
      ),
    )

    // Act
    render(<UserDetailDrawer />)

    // Assert
    await waitFor(() => {
      expect(screen.getByText('No encontrado')).toBeInTheDocument()
    })
  })

  it('Given el drawer abierto When cerrar Then navega a /users', async () => {
    // Arrange
    state.search = 'user=usr_01'
    render(<UserDetailDrawer />)
    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument()
    })

    // Act
    await userEvent.click(screen.getByRole('button', { name: /close/i }))

    // Assert
    expect(replaceMock).toHaveBeenCalledWith('/users')
  })
})
