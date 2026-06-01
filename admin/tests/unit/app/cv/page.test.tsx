import { render, screen } from '@tests/utils/render'
import { describe, expect, it } from 'vitest'
import CvManagementPage from '@/app/(admin)/cv/page'

/**
 * @module tests/unit/app/cv/page
 * @description Verifica que el placeholder de gestion de CV renderiza el titulo
 *   y el aviso "Proximamente".
 */
describe('CvManagementPage', () => {
  it('Given el placeholder When render Then muestra el titulo Gestion de CV', () => {
    // Arrange + Act
    render(<CvManagementPage />)

    // Assert
    expect(
      screen.getByRole('heading', { name: 'Gestion de CV' }),
    ).toBeInTheDocument()
  })

  it('Given el placeholder When render Then muestra el aviso Proximamente', () => {
    // Arrange + Act
    render(<CvManagementPage />)

    // Assert
    expect(screen.getByText('Proximamente')).toBeInTheDocument()
  })
})
