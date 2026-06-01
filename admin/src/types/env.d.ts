/** @config env.d.ts — type-safe NEXT_PUBLIC_* (complementa next-env.d.ts). */
declare namespace NodeJS {
  interface ProcessEnv {
    NEXT_PUBLIC_API_ENDPOINT: string
    NEXT_PUBLIC_TURNSTILE_SITEKEY: string
    NEXT_PUBLIC_ADMIN_URL: string
    NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS?: string
    NEXT_PUBLIC_WEBAUTHN_RP_ID: string
    NEXT_PUBLIC_FEATURE_MFA?: string
    NEXT_PUBLIC_USE_MSW?: string
  }
}
