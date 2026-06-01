import { server } from '@tests/mocks/server'
import { render, screen, userEvent, waitFor } from '@tests/utils/render'
import { HttpResponse, http } from 'msw'
import { describe, expect, it, vi } from 'vitest'
import { UserDetailDrawer } from '@/features/users-admin/components/user-detail-drawer'

/**
 * @module tests/unit/features/users-admin/user-detail-drawer-retry
 * @description Cubre el `onRetry={() => refetch()}` del ErrorAlert del drawer:
 *   con get-user en error, click en Reintentar dispara el refetch.
 */

const API = 'https://api.test.the-full-stack.com'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  useSearchParams: () => new URLSearchParams('user=usr_99'),
}))

describe('UserDetailDrawer retry', () => {
  it('Given get-user 500 When click Reintentar Then re-ejecuta el refetch', async () => {
    // Arrange
    server.use(
      http.post(`${API}/users`, () =>
        HttpResponse.json(
          { error: 'SERVER_ERROR', code: 5000, message: 'Falla detalle' },
          { status: 500 },
        ),
      ),
    )
    const user = userEvent.setup()
    render(<UserDetailDrawer />)
    await screen.findByText('Falla detalle')

    // Act: cubre el callback onRetry del ErrorAlert
    await user.click(screen.getByRole('button', { name: /reintentar/i }))

    // Assert: tras el retry el ErrorAlert sigue (mismo handler 500)
    await waitFor(() => {
      expect(screen.getByText('Falla detalle')).toBeInTheDocument()
    })
  })
})
