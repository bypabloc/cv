import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { type RenderOptions, render as rtlRender } from '@testing-library/react'
import { ThemeProvider } from 'next-themes'
import type { ReactElement, ReactNode } from 'react'
import { Toaster } from 'sonner'

/**
 * @module tests/utils/render
 * @description Render wrapper con providers (Theme + QueryClient de test +
 *   Toaster). El QueryClient se recrea por render (sin cache entre tests).
 */

function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  })
}

function Wrapper({ children }: { children: ReactNode }) {
  const client = createTestQueryClient()
  return (
    <ThemeProvider attribute="data-theme" defaultTheme="dark">
      <QueryClientProvider client={client}>
        {children}
        <Toaster />
      </QueryClientProvider>
    </ThemeProvider>
  )
}

export function render(ui: ReactElement, options?: RenderOptions) {
  return rtlRender(ui, { wrapper: Wrapper, ...options })
}

export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'
