'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { useChangeEmailInitiate } from '../hooks/use-change-email'
import { type ChangeEmailInput, changeEmailSchema } from '../validation'

/**
 * @component ChangeEmailForm
 * @description Inicia el cambio de email (users.profile.change-email). Tras el
 *   envio muestra el estado "revisa tu correo". La confirmacion (con el token)
 *   la maneja `ConfirmEmailChange`.
 */
export function ChangeEmailForm() {
  const changeEmail = useChangeEmailInitiate()

  const form = useForm<ChangeEmailInput>({
    resolver: zodResolver(changeEmailSchema),
    defaultValues: { new_email: '' },
  })

  const onSubmit = form.handleSubmit((values) => {
    changeEmail.mutate({ new_email: values.new_email })
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cambiar email</CardTitle>
        <CardDescription>
          Te enviaremos un correo de confirmacion al nuevo email.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {changeEmail.isSuccess ? (
          <p className="text-sm text-muted-foreground" role="status">
            Revisa tu correo para confirmar el cambio de email.
          </p>
        ) : (
          <Form {...form}>
            <form onSubmit={onSubmit} className="space-y-4" noValidate>
              <FormField
                control={form.control}
                name="new_email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nuevo email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        autoComplete="email"
                        placeholder="nuevo@ejemplo.com"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" disabled={changeEmail.isPending}>
                {changeEmail.isPending ? 'Enviando...' : 'Enviar confirmacion'}
              </Button>
            </form>
          </Form>
        )}
      </CardContent>
    </Card>
  )
}
