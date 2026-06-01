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
import { type SetPasswordInput, setPasswordSchema } from '@/lib/validation/auth'
import { useSetPassword } from '../hooks/use-set-password'
import { useAuthStore } from '../store/use-auth-store'

/**
 * @component SetPasswordForm
 * @description Form de set-password en el onboarding: password + confirmacion
 *   (Zod refine). Dispara verify.set-password con el temp_token del store.
 */
export function SetPasswordForm() {
  const tempToken = useAuthStore((s) => s.tempToken)
  const setPassword = useSetPassword()

  const form = useForm<SetPasswordInput>({
    resolver: zodResolver(setPasswordSchema),
    defaultValues: { password: '', confirm: '' },
  })

  const onSubmit = form.handleSubmit((values) => {
    if (!tempToken) return
    setPassword.mutate({ password: values.password, temp_token: tempToken })
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
                <Input type="password" autoComplete="new-password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="confirm"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Confirmar contrasena</FormLabel>
              <FormControl>
                <Input type="password" autoComplete="new-password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button
          type="submit"
          className="w-full"
          disabled={setPassword.isPending || !tempToken}
        >
          {setPassword.isPending ? 'Guardando...' : 'Guardar contrasena'}
        </Button>
      </form>
    </Form>
  )
}
