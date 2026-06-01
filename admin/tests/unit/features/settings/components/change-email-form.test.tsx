import { render, screen, userEvent, waitFor } from '@tests/utils/render'
import type { ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { ChangeEmailForm } from '@/features/settings/components/change-email-form'

/**
 * @module tests/unit/features/settings/components/change-email-form
 * @description Verifica que un email invalido lo bloquea Zod, y que un email
 *   valido inicia el flow (users.profile.change-email) y muestra el estado
 *   "revisa tu correo".
 */

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}))

describe('ChangeEmailForm', () => {
  it('Given email invalido When submit Then Zod bloquea (no muestra estado)', async () => {
    // Arrange
    const user = userEvent.setup()
    render((<ChangeEmailForm />) as ReactElement)

    // Act
    await user.type(screen.getByLabelText(/nuevo email/i), 'no-es-email')
    await user.click(
      screen.getByRole('button', { name: /enviar confirmacion/i }),
    )

    // Assert
    await waitFor(() => {
      expect(screen.getByText(/email invalido/i)).toBeInTheDocument()
    })
    expect(screen.queryByText(/revisa tu correo/i)).not.toBeInTheDocument()
  })

  it('Given email valido When submit Then muestra estado revisa tu correo', async () => {
    // Arrange
    const user = userEvent.setup()
    render((<ChangeEmailForm />) as ReactElement)

    // Act
    await user.type(screen.getByLabelText(/nuevo email/i), 'nuevo@test.com')
    await user.click(
      screen.getByRole('button', { name: /enviar confirmacion/i }),
    )

    // Assert
    await waitFor(() => {
      expect(
        screen.getByText(/revisa tu correo para confirmar el cambio/i),
      ).toBeInTheDocument()
    })
  })
})
