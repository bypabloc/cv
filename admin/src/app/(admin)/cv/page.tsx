'use client'

import { FileText } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

/**
 * @page CvManagementPage
 * @description Placeholder de la gestion de CV. SIN backend ni UI de edicion en
 *   este plan: la edicion se entregara en el plan futuro `c-cv-management`.
 */
export default function CvManagementPage() {
  return (
    <section className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl font-semibold">Gestion de CV</h1>
      <Alert>
        <FileText className="h-4 w-4" />
        <AlertTitle>Proximamente</AlertTitle>
        <AlertDescription>
          La edicion del CV se entregara en el plan futuro c-cv-management.
        </AlertDescription>
      </Alert>
    </section>
  )
}
