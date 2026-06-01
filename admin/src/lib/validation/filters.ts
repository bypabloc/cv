import { z } from 'zod'

/**
 * @module validation/filters
 * @description Zod schemas reusables para filtros (rango de fechas,
 *   paginacion). Usados por las tablas/listas del admin.
 */

export const dateRangeSchema = z.object({
  from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Fecha invalida'),
  to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Fecha invalida'),
})
export type DateRange = z.infer<typeof dateRangeSchema>

export const paginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  page_size: z.coerce.number().int().min(1).max(200).default(50),
})
export type Pagination = z.infer<typeof paginationSchema>
