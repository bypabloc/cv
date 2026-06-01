/**
 * @module features/auth/api/query-keys
 * @description Query keys estructurados de Tanstack Query para el dominio auth.
 *   Las mutations invalidan estas keys; las queries las consumen.
 */
export const authKeys = {
  all: ['auth'] as const,
  user: () => [...authKeys.all, 'user'] as const,
  methods: (email: string) => [...authKeys.all, 'methods', email] as const,
  mfa: () => [...authKeys.all, 'mfa'] as const,
  webauthn: () => [...authKeys.all, 'webauthn'] as const,
}
