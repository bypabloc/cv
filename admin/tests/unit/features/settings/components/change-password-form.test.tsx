import { render, screen, userEvent, waitFor } from '@tests/utils/render'
import type { ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { ChangePasswordForm } from '@/features/settings/components/change-password-form'

/**
 * @module tests/unit/features/settings/components/change-password-form
 * @description Verifica el Zod refine (longitud min 12 + match new===confirm),
 *   el camino feliz (toast 'Contrasena actualizada' contra la action REAL) y
 *   el 401 INVALID_PASSWORD (current incorrecta 'wrong-current-pass' -> toast
 *   inline, NO rompe).
 */

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}))

describe('ChangePasswordForm', () => {
  it('Given new_password corta When submit Then Zod bloquea (min 12)', async () => {
    // Arrange
    const user = userEvent.setup()
    render((<ChangePasswordForm />) as ReactElement)

    // Act
    await user.type(screen.getByLabelText(/contrasena actual/i), 'old-pass-123')
    await user.type(screen.getByLabelText(/^nueva contrasena$/i), 'corta')
    await user.type(
      screen.getByLabelText(/confirmar nueva contrasena/i),
      'corta',
    )
    await user.click(
      screen.getByRole('button', { name: /actualizar contrasena/i }),
    )

    // Assert
    await waitFor(() => {
      expect(screen.getByText(/al menos 12 caracteres/i)).toBeInTheDocument()
    })
  })

  it('Given new_password != confirm When submit Then Zod bloquea (no coinciden)', async () => {
    // Arrange
    const user = userEvent.setup()
    render((<ChangePasswordForm />) as ReactElement)

    // Act
    await user.type(screen.getByLabelText(/contrasena actual/i), 'old-pass-123')
    await user.type(
      screen.getByLabelText(/^nueva contrasena$/i),
      'nueva-pass-larga-1',
    )
    await user.type(
      screen.getByLabelText(/confirmar nueva contrasena/i),
      'otra-pass-larga-9',
    )
    await user.click(
      screen.getByRole('button', { name: /actualizar contrasena/i }),
    )

    // Assert
    await waitFor(() => {
      expect(screen.getByText(/no coinciden/i)).toBeInTheDocument()
    })
  })

  it('Given datos validos When submit Then muestra toast Contrasena actualizada', async () => {
    // Arrange
    const user = userEvent.setup()
    render((<ChangePasswordForm />) as ReactElement)

    // Act
    await user.type(screen.getByLabelText(/contrasena actual/i), 'old-pass-123')
    await user.type(
      screen.getByLabelText(/^nueva contrasena$/i),
      'nueva-pass-larga-1',
    )
    await user.type(
      screen.getByLabelText(/confirmar nueva contrasena/i),
      'nueva-pass-larga-1',
    )
    await user.click(
      screen.getByRole('button', { name: /actualizar contrasena/i }),
    )

    // Assert: la action REAL del MSW responde 200 con {ok:true}
    await waitFor(() => {
      expect(screen.getByText('Contrasena actualizada')).toBeInTheDocument()
    })
  })

  it('Given current incorrecta When submit Then 401 inline NO rompe (toast)', async () => {
    // Arrange
    const user = userEvent.setup()
    render((<ChangePasswordForm />) as ReactElement)

    // Act: 'wrong-current-pass' -> MSW responde 401 INVALID_PASSWORD
    await user.type(
      screen.getByLabelText(/contrasena actual/i),
      'wrong-current-pass',
    )
    await user.type(
      screen.getByLabelText(/^nueva contrasena$/i),
      'nueva-pass-larga-1',
    )
    await user.type(
      screen.getByLabelText(/confirmar nueva contrasena/i),
      'nueva-pass-larga-1',
    )
    await user.click(
      screen.getByRole('button', { name: /actualizar contrasena/i }),
    )

    // Assert
    await waitFor(() => {
      expect(
        screen.getByText(/la contrasena actual es incorrecta/i),
      ).toBeInTheDocument()
    })
    // El form sigue montado (no rompio)
    expect(
      screen.getByRole('button', { name: /actualizar contrasena/i }),
    ).toBeInTheDocument()
  })
})
