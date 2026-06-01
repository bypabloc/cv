'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import {
  type LoginPasswordInput as LoginPasswordValues,
  loginPasswordSchema,
} from '@/lib/validation/auth'
import type { TempTokenResponse } from '@/types/api'
import { useLoginVerifyPassword } from '../hooks/use-login-verify-password'
import { useAuthStore } from '../store/use-auth-store'

type Methods = NonNullable<TempTokenResponse['methods']>

/**
 * @component LoginPasswordInput
 * @description Paso `login.verify-password` (password min 12). Sin MFA el hook
 *   cierra el login; con MFA llama `onMfaRequired(methods)` para avanzar al
 *   paso TOTP/recovery. Usa el temp_token del store.
 *
 * @props {(methods: Methods) => void} [onMfaRequired] - MFA pendiente
 */
export function LoginPasswordInput({
  onMfaRequired,
}: {
  onMfaRequired?: (methods: Methods) => void
}) {
  const tempToken = useAuthStore((s) => s.tempToken)
  const verifyPassword = useLoginVerifyPassword({ onMfaRequired })

  const form = useForm<LoginPasswordValues>({
    resolver: zodResolver(loginPasswordSchema),
    defaultValues: { password: '' },
  })

  const onSubmit = form.handleSubmit((values) => {
    if (!tempToken) return
    verifyPassword.mutate({ password: values.password, temp_token: tempToken })
  })

  return (
    <Form {...form}>
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Contrasena</FormLabel>
              <FormControl>
                <Input
                  type="password"
                  autoComplete="current-password"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button
          type="submit"
          className="w-full"
          disabled={verifyPassword.isPending || !tempToken}
        >
          {verifyPassword.isPending ? 'Verificando...' : 'Continuar'}
        </Button>
      </form>
    </Form>
  )
}
