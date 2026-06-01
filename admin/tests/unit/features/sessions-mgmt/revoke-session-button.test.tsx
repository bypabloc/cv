import { makeJwt } from '@tests/mocks/jwt'
import { server } from '@tests/mocks/server'
import { render, screen, userEvent, waitFor } from '@tests/utils/render'
import { HttpResponse, http } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'
import { useAuthStore } from '@/features/auth/store/use-auth-store'
import { RevokeSessionButton } from '@/features/sessions-mgmt/components/revoke-session-button'
import type { User } from '@/types/models'

const API = 'https://api.test.the-full-stack.com'

/**
 * @module tests/unit/features/sessions-mgmt/revoke-session-button
 * @description Boton de revocar: deshabilitado en la sesion actual; ante el
 *   400 CANNOT_REVOKE_CURRENT_SESSION muestra el error inline; revocar otra
 *   sesion resuelve sin error.
 */

const USER: User = {
  id: 'usr_01',
  email: 'user@test.com',
  status: 'active',
  display_name: 'Pablo',
  has_password: true,
  mfa_methods: ['totp'],
}

beforeEach(() => {
  // Token presente para que el api-client agregue el Bearer (defensa: el
  // backend MSW no requiere el header, pero el flujo real si lo usa).
  useAuthStore.setState({ accessToken: makeJwt({ sub: 'usr_01' }), user: USER })
})

describe('RevokeSessionButton', () => {
  it('Given isCurrent true When se renderiza Then el boton esta deshabilitado', () => {
    // Arrange + Act
    render(<RevokeSessionButton sessionId="sess_current" isCurrent />)

    // Assert
    expect(screen.getByRole('button', { name: 'Revocar' })).toBeDisabled()
  })

  it('Given la sesion actual When se intenta revocar (400) Then muestra el error inline y no rompe', async () => {
    // Arrange: isCurrent false fuerza el path 400 del backend con sess_current
    const user = userEvent.setup()
    render(<RevokeSessionButton sessionId="sess_current" isCurrent={false} />)

    // Act
    await user.click(screen.getByRole('button', { name: 'Revocar' }))

    // Assert
    const error = await screen.findByRole('alert')
    expect(error).toHaveTextContent('No puedes revocar la sesion actual')
  })

  it('Given otra sesion When se revoca Then resuelve sin mostrar error inline', async () => {
    // Arrange
    const user = userEvent.setup()
    render(<RevokeSessionButton sessionId="sess_other" isCurrent={false} />)

    // Act
    await user.click(screen.getByRole('button', { name: 'Revocar' }))

    // Assert
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Revocar' })).toBeEnabled()
    })
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('Given un error 500 del backend When se revoca Then muestra el mensaje generico inline', async () => {
    // Arrange: override del handler para forzar un error no-400
    server.use(
      http.post(`${API}/users`, () =>
        HttpResponse.json(
          { error: 'INTERNAL', code: 6000, message: 'Error interno' },
          { status: 500 },
        ),
      ),
    )
    const user = userEvent.setup()
    render(<RevokeSessionButton sessionId="sess_other" isCurrent={false} />)

    // Act
    await user.click(screen.getByRole('button', { name: 'Revocar' }))

    // Assert
    const error = await screen.findByRole('alert')
    expect(error).toHaveTextContent('Error interno')
  })
})
