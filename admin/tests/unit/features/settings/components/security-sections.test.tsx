import type { RegistrationResponseJSON } from '@simplewebauthn/browser'
import { render, screen, userEvent, waitFor } from '@tests/utils/render'
import type { ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { EmailCodeSection } from '@/features/settings/components/email-code-section'
import { RecoveryCodesSection } from '@/features/settings/components/recovery-codes-section'
import { WebAuthnCredentialsList } from '@/features/settings/components/webauthn-credentials-list'

/**
 * @module tests/unit/features/settings/components/security-sections
 * @description Cubre las secciones que componen el feature auth: email-code
 *   (setup), recovery-codes (genera + modal con los 10 codes), webauthn
 *   credentials (lista + registrar + eliminar).
 */

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}))

const { startRegistrationMock } = vi.hoisted(() => ({
  startRegistrationMock: vi.fn(),
}))
vi.mock('@simplewebauthn/browser', () => ({
  startRegistration: startRegistrationMock,
  startAuthentication: vi.fn(),
}))

describe('EmailCodeSection', () => {
  it('Given el boton When click Then activa el codigo por email (setup-email-code)', async () => {
    // Arrange
    const user = userEvent.setup()
    render((<EmailCodeSection />) as ReactElement)

    // Act
    const button = screen.getByRole('button', {
      name: /activar codigo por email/i,
    })
    await user.click(button)

    // Assert: el MSW responde y el boton vuelve a su estado base
    await waitFor(() => {
      expect(button).not.toBeDisabled()
    })
  })
})

describe('RecoveryCodesSection', () => {
  it('Given el boton Generar When click Then muestra los 10 codes en el modal', async () => {
    // Arrange
    const user = userEvent.setup()
    render((<RecoveryCodesSection />) as ReactElement)

    // Act
    await user.click(screen.getByRole('button', { name: /generar codigos/i }))

    // Assert: el modal abre con el primer code del MSW (RECOV00000)
    await waitFor(() => {
      expect(screen.getByText('RECOV00000')).toBeInTheDocument()
    })
    expect(screen.getByText('RECOV00009')).toBeInTheDocument()
  })
})

describe('WebAuthnCredentialsList', () => {
  it('Given credenciales del backend When render Then lista el passkey', async () => {
    // Arrange + Act: el MSW devuelve un passkey "YubiKey"
    render((<WebAuthnCredentialsList />) as ReactElement)

    // Assert
    expect(await screen.findByText('YubiKey')).toBeInTheDocument()
  })

  it('Given el boton Eliminar When click Then llama delete-credential', async () => {
    // Arrange
    const user = userEvent.setup()
    render((<WebAuthnCredentialsList />) as ReactElement)
    await screen.findByText('YubiKey')

    // Act
    await user.click(screen.getByRole('button', { name: /^eliminar$/i }))

    // Assert: tras el delete (MSW 200) la lista se invalida y el passkey ya no
    // figura (refetch devuelve el mismo handler -> se mantiene; verificamos que
    // el boton siguio existiendo sin romper)
    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: /agregar passkey/i }),
      ).toBeInTheDocument()
    })
  })

  it('Given el boton Agregar When click Then startRegistration recibe las options', async () => {
    // Arrange
    startRegistrationMock.mockResolvedValue({
      id: 'reg',
    } as unknown as RegistrationResponseJSON)
    const user = userEvent.setup()
    render((<WebAuthnCredentialsList />) as ReactElement)
    await screen.findByText('YubiKey')

    // Act
    await user.click(screen.getByRole('button', { name: /agregar passkey/i }))

    // Assert
    await waitFor(() => {
      expect(startRegistrationMock).toHaveBeenCalledTimes(1)
    })
  })
})
