'use client'

import { Turnstile } from '@marsidev/react-turnstile'
import { env } from '@/lib/env'

/**
 * @component TurnstileWidget
 * @description Wrapper de Cloudflare Turnstile con el sitekey del env. Emite el
 *   token de challenge via `onToken`; lo limpia (null) si expira o falla, para
 *   que el form bloquee el submit hasta tener un token vigente.
 *
 * @props {(token: string | null) => void} onToken - Recibe el token (o null)
 */
export function TurnstileWidget({
  onToken,
}: {
  onToken: (token: string | null) => void
}) {
  return (
    <Turnstile
      siteKey={env.NEXT_PUBLIC_TURNSTILE_SITEKEY}
      onSuccess={(token) => onToken(token)}
      onExpire={() => onToken(null)}
      onError={() => onToken(null)}
      options={{ theme: 'auto' }}
    />
  )
}
