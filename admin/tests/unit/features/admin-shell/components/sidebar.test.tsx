import { render, screen } from '@tests/utils/render'
import { describe, expect, it, vi } from 'vitest'
import { Sidebar } from '@/features/admin-shell/components/sidebar'

vi.mock('next/navigation', () => ({
  usePathname: () => '/settings',
}))

describe('Sidebar', () => {
  it('Given pathname /settings When render Then el item Configuracion esta activo', () => {
    // Arrange + Act
    render(<Sidebar />)

    // Assert
    const link = screen.getByRole('link', { name: /configuracion/i })
    expect(link.className).toContain('bg-accent')
  })

  it('Given pathname /settings When render Then el item Metricas NO esta activo', () => {
    // Arrange + Act
    render(<Sidebar />)

    // Assert
    const link = screen.getByRole('link', { name: /metricas/i })
    expect(link.className).toContain('text-muted-foreground')
  })

  it('Given el sidebar When render Then muestra los 5 items de navegacion', () => {
    // Arrange + Act
    render(<Sidebar />)

    // Assert
    expect(screen.getAllByRole('link')).toHaveLength(5)
  })
})
