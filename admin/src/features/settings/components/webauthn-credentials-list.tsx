'use client'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { ErrorAlert } from '@/components/ui/error-alert'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Separator } from '@/components/ui/separator'
import {
  useDeleteCredential,
  useListCredentials,
  WebAuthnRegisterButton,
} from '@/features/auth'
import { formatDate } from '@/lib/format/date'

/**
 * @component WebAuthnCredentialsList
 * @description Compone los hooks/componentes WebAuthn del feature `auth`: lista
 *   los passkeys (useListCredentials), permite registrar uno nuevo
 *   (WebAuthnRegisterButton) y borrar (useDeleteCredential). El guard
 *   MUST_KEEP_ONE_MFA_METHOD responde 409 si dejaria total_mfa === 0
 *   (lo maneja useDeleteCredential mostrando el error inline).
 */
export function WebAuthnCredentialsList() {
  const credentials = useListCredentials()
  const deleteCredential = useDeleteCredential()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Passkeys (WebAuthn)</CardTitle>
        <CardDescription>
          Inicia sesion con tu dispositivo, biometria o llave de seguridad.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {credentials.isLoading ? (
          <LoadingSpinner />
        ) : credentials.isError || !credentials.data ? (
          <ErrorAlert
            error={credentials.error}
            onRetry={() => credentials.refetch()}
          />
        ) : credentials.data.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No tienes passkeys registrados.
          </p>
        ) : (
          <ul className="space-y-3">
            {credentials.data.map((credential) => (
              <li
                key={credential.id}
                className="flex items-center justify-between gap-3 rounded-md border p-3"
              >
                <div className="space-y-0.5">
                  <p className="text-sm font-medium">
                    {credential.nickname ?? 'Passkey'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Ultimo uso: {formatDate(credential.last_used_at)}
                  </p>
                </div>
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  disabled={deleteCredential.isPending}
                  onClick={() =>
                    deleteCredential.mutate({ credential_id: credential.id })
                  }
                >
                  Eliminar
                </Button>
              </li>
            ))}
          </ul>
        )}

        <Separator />
        <WebAuthnRegisterButton />
      </CardContent>
    </Card>
  )
}
