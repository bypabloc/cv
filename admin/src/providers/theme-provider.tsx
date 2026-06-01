'use client'

import { ThemeProvider as NextThemesProvider } from 'next-themes'
import type { ReactNode } from 'react'

/**
 * @component ThemeProvider
 * @description next-themes con `data-theme` + system/dark/light.
 *   defaultTheme="system" respeta prefers-color-scheme la primera visita;
 *   el toggle persiste la eleccion en localStorage (clave `theme`).
 *   disableTransitionOnChange evita el flicker al cambiar de tema.
 *
 * @props {ReactNode} children - Arbol de la app
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  return (
    <NextThemesProvider
      attribute="data-theme"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      {children}
    </NextThemesProvider>
  )
}
