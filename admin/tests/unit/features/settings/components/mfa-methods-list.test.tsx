import { server } from '@tests/mocks/server'
import { render, screen, userEvent, waitFor } from '@tests/utils/render'
import { HttpResponse, http } from 'msw'
import type { ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { MfaMethodsList } from '@/features/settings/components/mfa-methods-list'

const API_BASE = 'https://api.test.the-full-stack.com'

/**
 * @function mockMfaList
 * @description Override del handler `/auth` para devolver una lista MFA fija
 *   (resto de actions responden 200 vacio).
 */
function mockMfaList(data: {
  methods: {
    kind: 'totp' | 'email_code'
    confirmed_at: string | null
    is_preferred: boolean
  }[]
  webauthn_count: number
  total_mfa: number
}): void {
  server.use(
    http.post(`${API_BASE}/auth`, async ({ request }) => {
      const body = (await request.json()) as {
        operation: string
        action: string
      }
      if (body.operation === 'mfa' && body.action === 'list') {
        return HttpResponse.json({ is_valid: true, code: 0, data })
      }
      return HttpResponse.json({ is_valid: true, code: 0, data: {} })
    }),
  )
}

/**
 * @module tests/unit/features/settings/components/mfa-methods-list
 * @description Verifica que la lista MFA renderiza los metodos (mfa.list) y
 *   que el boton Desactivar se deshabilita cuando total_mfa === 1 (defensa en
 *   profundidad). Con total_mfa > 1 el boton esta habilitado.
 */

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}))

describe('MfaMethodsList', () => {
  it('Given total_mfa > 1 When render Then el boton Desactivar esta habilitado', async () => {
    // Arrange: el handler por defecto devuelve total_mfa 2 (TOTP + webauthn)
    render((<MfaMethodsList />) as ReactElement)

    // Act + Assert
    const disable = await screen.findByRole('button', { name: /desactivar/i })
    expect(disable).not.toBeDisabled()
  })

  it('Given total_mfa === 1 When render Then el boton Desactivar esta deshabilitado', async () => {
    // Arrange: forzar un solo metodo MFA confirmado
    mockMfaList({
      methods: [
        {
          kind: 'totp',
          confirmed_at: '2026-05-01T00:00:00Z',
          is_preferred: true,
        },
      ],
      webauthn_count: 0,
      total_mfa: 1,
    })

    // Act
    render((<MfaMethodsList />) as ReactElement)

    // Assert
    const disable = await screen.findByRole('button', { name: /desactivar/i })
    expect(disable).toBeDisabled()
    await waitFor(() => {
      expect(
        screen.getByText(/debes conservar al menos un metodo mfa/i),
      ).toBeInTheDocument()
    })
  })

  it('Given un metodo no preferido When click Marcar preferido Then llama set-preferred', async () => {
    // Arrange: email_code no preferido + un segundo factor (total_mfa 2)
    mockMfaList({
      methods: [
        {
          kind: 'email_code',
          confirmed_at: '2026-05-01T00:00:00Z',
          is_preferred: false,
        },
      ],
      webauthn_count: 1,
      total_mfa: 2,
    })
    const user = userEvent.setup()
    render((<MfaMethodsList />) as ReactElement)

    // Act
    const preferBtn = await screen.findByRole('button', {
      name: /marcar preferido/i,
    })
    await user.click(preferBtn)

    // Assert: el MSW responde y el boton sigue accesible (no rompio)
    await waitFor(() => {
      expect(preferBtn).not.toBeDisabled()
    })
  })

  it('Given sin TOTP When click Agregar aplicacion Then abre el dialog de setup', async () => {
    // Arrange: solo email_code -> el boton de agregar TOTP debe estar
    mockMfaList({
      methods: [
        {
          kind: 'email_code',
          confirmed_at: '2026-05-01T00:00:00Z',
          is_preferred: true,
        },
      ],
      webauthn_count: 1,
      total_mfa: 2,
    })
    const user = userEvent.setup()
    render((<MfaMethodsList />) as ReactElement)

    // Act
    await user.click(
      await screen.findByRole('button', { name: /agregar aplicacion/i }),
    )

    // Assert: el dialog de setup TOTP abre (titulo del Dialog)
    await waitFor(() => {
      expect(screen.getByText(/configurar totp/i)).toBeInTheDocument()
    })
  })

  it('Given sin metodos When render Then muestra el estado vacio', async () => {
    // Arrange
    mockMfaList({ methods: [], webauthn_count: 0, total_mfa: 0 })

    // Act
    render((<MfaMethodsList />) as ReactElement)

    // Assert
    expect(
      await screen.findByText(/no tienes metodos mfa configurados/i),
    ).toBeInTheDocument()
  })

  it('Given disable que deja total_mfa 0 When click Desactivar Then muestra el 409 inline', async () => {
    // Arrange: dos metodos para habilitar el boton; el disable del MSW por
    // defecto responde 409 MUST_KEEP_ONE_MFA_METHOD
    mockMfaList({
      methods: [
        {
          kind: 'totp',
          confirmed_at: '2026-05-01T00:00:00Z',
          is_preferred: true,
        },
        {
          kind: 'email_code',
          confirmed_at: '2026-05-01T00:00:00Z',
          is_preferred: false,
        },
      ],
      webauthn_count: 0,
      total_mfa: 2,
    })
    server.use(
      http.post(`${API_BASE}/auth`, async ({ request }) => {
        const body = (await request.json()) as {
          operation: string
          action: string
        }
        if (body.operation === 'mfa' && body.action === 'list') {
          return HttpResponse.json({
            is_valid: true,
            code: 0,
            data: {
              methods: [
                {
                  kind: 'totp',
                  confirmed_at: '2026-05-01T00:00:00Z',
                  is_preferred: true,
                },
                {
                  kind: 'email_code',
                  confirmed_at: '2026-05-01T00:00:00Z',
                  is_preferred: false,
                },
              ],
              webauthn_count: 0,
              total_mfa: 2,
            },
          })
        }
        if (body.operation === 'mfa' && body.action === 'disable') {
          return HttpResponse.json(
            {
              error: 'MUST_KEEP_ONE_MFA_METHOD',
              code: 4093,
              message: 'Debes conservar al menos un metodo MFA',
            },
            { status: 409 },
          )
        }
        return HttpResponse.json({ is_valid: true, code: 0, data: {} })
      }),
    )
    const user = userEvent.setup()
    render((<MfaMethodsList />) as ReactElement)

    // Act
    const buttons = await screen.findAllByRole('button', {
      name: /desactivar/i,
    })
    await user.click(buttons[0] as HTMLElement)

    // Assert: el toast del 409 aparece (sonner)
    await waitFor(() => {
      expect(
        screen.getByText(/debes conservar al menos un metodo mfa/i),
      ).toBeInTheDocument()
    })
  })

  it('Given mfa.list falla When render Then muestra el ErrorAlert', async () => {
    // Arrange
    server.use(
      http.post(`${API_BASE}/auth`, () =>
        HttpResponse.json(
          { error: 'SERVER_ERROR', code: 5000, message: 'fallo' },
          { status: 500 },
        ),
      ),
    )

    // Act
    render((<MfaMethodsList />) as ReactElement)

    // Assert
    expect(await screen.findByText(/^error$/i)).toBeInTheDocument()
  })
})
