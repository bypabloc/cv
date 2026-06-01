import { render, screen, userEvent, waitFor } from '@tests/utils/render'
import type { ReactElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { RecoveryCodesModal } from '@/features/auth/components/recovery-codes-modal'

/**
 * @module tests/unit/features/auth/components/recovery-codes-modal
 * @description Verifica que liste los 10 codes y que "Ya los guarde" cierre.
 */

const CODES = Array.from({ length: 10 }, (_, i) => `CODE${i}`)

describe('RecoveryCodesModal', () => {
  it('Given 10 codes When open Then los muestra todos', () => {
    render(
      (
        <RecoveryCodesModal open codes={CODES} onClose={vi.fn()} />
      ) as ReactElement,
    )

    for (const code of CODES) {
      expect(screen.getByText(code)).toBeInTheDocument()
    }
  })

  it('Given el modal abierto When click "Ya los guarde" Then llama onClose', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(
      (
        <RecoveryCodesModal open codes={CODES} onClose={onClose} />
      ) as ReactElement,
    )

    await user.click(screen.getByRole('button', { name: /ya los guarde/i }))

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('Given click Copiar Then escribe los codes en el clipboard', async () => {
    const user = userEvent.setup()
    // userEvent.setup() instala su propio clipboard; lo sobreescribimos despues.
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    })
    render(
      (
        <RecoveryCodesModal open codes={CODES} onClose={vi.fn()} />
      ) as ReactElement,
    )

    await user.click(screen.getByRole('button', { name: /copiar/i }))

    await waitFor(() => {
      expect(writeText).toHaveBeenCalledWith(CODES.join('\n'))
    })
  })

  it('Given el modal abierto When se cierra con Escape Then onOpenChange(false) llama onClose', async () => {
    // Arrange
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(
      (
        <RecoveryCodesModal open codes={CODES} onClose={onClose} />
      ) as ReactElement,
    )

    // Act: Escape dispara onOpenChange(false) -> rama `!next && onClose()`
    await user.keyboard('{Escape}')

    // Assert
    await waitFor(() => {
      expect(onClose).toHaveBeenCalledTimes(1)
    })
  })

  it('Given click Descargar Then genera un blob URL', async () => {
    const createObjectURL = vi.fn().mockReturnValue('blob:fake')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL })
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => {})
    const user = userEvent.setup()
    render(
      (
        <RecoveryCodesModal open codes={CODES} onClose={vi.fn()} />
      ) as ReactElement,
    )

    await user.click(screen.getByRole('button', { name: /descargar/i }))

    expect(createObjectURL).toHaveBeenCalledTimes(1)
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:fake')
    clickSpy.mockRestore()
    vi.unstubAllGlobals()
  })
})
