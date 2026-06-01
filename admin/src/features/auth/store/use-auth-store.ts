import { jwtDecode } from 'jwt-decode'
import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'
import type { User } from '@/types/models'

/**
 * @module use-auth-store
 * @description Store de auth (Zustand + persist).
 *
 * Persistencia (decision 4 del plan):
 * - `refreshToken`, `refreshExpiry`, `user` -> localStorage (sobreviven reload).
 * - `accessToken` -> SOLO memoria (rota en cada refresh; persistirlo deja
 *   stale token tras reload).
 * - `tempToken` -> SOLO memoria (efimero, 5 min, flujo register/login).
 *
 * Bootstrap: al reload `accessToken === null`; `useAuthTimer` detecta
 * `refreshToken` con `refreshExpiry > now` y dispara `/session/refresh`.
 */

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  refreshExpiry: number | null
  tempToken: string | null
  user: User | null

  setTokens: (
    access: string,
    refresh: string,
    user: User,
    refreshExpiry?: number | null,
  ) => void
  setAccessToken: (token: string | null) => void
  setRefreshToken: (token: string | null) => void
  setTempToken: (token: string | null) => void
  setUser: (user: User | null) => void
  clearTokens: () => void
  reset: () => void

  isAuthenticated: () => boolean
  isAccessExpired: () => boolean
}

function decodeExp(token: string): number | null {
  try {
    const { exp } = jwtDecode<{ exp: number }>(token)
    return exp * 1000
  } catch {
    return null
  }
}

const EMPTY = {
  accessToken: null,
  refreshToken: null,
  refreshExpiry: null,
  tempToken: null,
  user: null,
} as const

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      ...EMPTY,

      setTokens: (access, refresh, user, refreshExpiry) =>
        set({
          accessToken: access,
          refreshToken: refresh,
          user,
          refreshExpiry: refreshExpiry ?? decodeExp(refresh),
        }),
      setAccessToken: (token) => set({ accessToken: token }),
      setRefreshToken: (token) =>
        set({
          refreshToken: token,
          refreshExpiry: token ? decodeExp(token) : null,
        }),
      setTempToken: (token) => set({ tempToken: token }),
      setUser: (user) => set({ user }),
      clearTokens: () => set({ ...EMPTY }),
      reset: () => set({ ...EMPTY }),

      isAuthenticated: () => {
        const { accessToken, user } = get()
        if (!accessToken || !user) return false
        return !get().isAccessExpired()
      },

      isAccessExpired: () => {
        const { accessToken } = get()
        if (!accessToken) return true
        const exp = decodeExp(accessToken)
        if (exp === null) return true
        return Date.now() >= exp
      },
    }),
    {
      name: 'portfolio-admin-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        refreshToken: state.refreshToken,
        refreshExpiry: state.refreshExpiry,
        user: state.user,
      }),
    },
  ),
)
