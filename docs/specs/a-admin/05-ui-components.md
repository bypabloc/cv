# 05 — UI components (referencia del knowledge tree)

[< 04-setup-base](04-setup-base.md) | [Siguiente: 06-auth-feature >](06-auth-feature.md)

## Aclaracion

Los componentes UI primitivos (shadcn + custom) ya quedaron creados en
la **fase 3-4** (ver 04-setup-base.md). Esta seccion documenta las
**reglas** que aplican al construir componentes en `src/features/<X>/
components/` y la integracion con Recharts / Tanstack Table / Virtual.

Ver detalle en `.claude/docs/admin/03-ui.md` (KT permanente).

## Reglas duras al construir componentes de feature

1. **SIEMPRE** componer sobre `components/ui/` primitives. NUNCA estilizar
   inline un primitivo con `className` sobre-escribiendo comportamiento
   base. Si necesitas otra variante: crear una nueva variant CVA en el
   primitivo.
2. **SIEMPRE** Client Components (`'use client'` en primera linea).
3. **SIEMPRE** props tipadas (`interface Props { ... }`).
4. **SIEMPRE** filename `kebab-case.tsx`, component `PascalCase`.
5. **SIEMPRE** si necesita data, recibirla por prop O usar el hook de
   la feature. NUNCA hacer fetch directo desde el componente.
6. **NUNCA** importar de otra feature (`features/B` desde `features/A`).
7. **NUNCA** atribucion a IA en docstrings ni JSX.

## Componentes de feature — patron

```tsx
// src/features/<feature>/components/<component>.tsx
'use client'

import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card'
import {MetricCard} from '@/components/ui/metric-card'
import {useOverviewQuery} from '../hooks/use-overview-query'
import {Skeleton} from '@/components/ui/skeleton'
import {ErrorAlert} from '@/components/ui/error-alert'

export function AnalyticsOverviewCards() {
  const {data, isLoading, isError, error, refetch} = useOverviewQuery()

  if (isError) return <ErrorAlert error={error} onRetry={() => refetch()} />

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      {(isLoading ? Array.from({length: 4}) : [
        {title: 'Sessions', value: data?.sessions ?? 0},
        {title: 'Visits', value: data?.visits ?? 0},
        {title: 'Events', value: data?.events ?? 0},
        {title: 'Contacts', value: data?.contacts ?? 0},
      ]).map((card, i) => (
        card === undefined ? (
          <Skeleton key={i} className="h-32" />
        ) : (
          <MetricCard
            key={card.title}
            title={card.title}
            value={String(card.value)}
          />
        )
      ))}
    </div>
  )
}
```

## Charts con shadcn + Recharts — patron

Ver `.claude/docs/admin/03-ui.md` para el ejemplo completo de
TimeseriesChart. Reglas:

- **SIEMPRE** colors via CSS vars (`hsl(var(--primary))`), NO hex.
- **SIEMPRE** envolver en `<ChartContainer config={...}>` para responsive
  + theming.
- **SIEMPRE** `<ChartTooltip content={<ChartTooltipContent />} />`.
- **NUNCA** `width` / `height` fijo en px (usar className con h-[300px]).

## Tanstack Table — patron

Usar el wrapper `DataTable` de `components/ui/`. Definir columnas en el
componente de feature:

```tsx
const columns: ColumnDef<Session>[] = [
  {accessorKey: 'session_id', header: 'Session'},
  {
    accessorKey: 'first_seen_at',
    header: 'Inicio',
    cell: ({row}) => formatDate(row.getValue('first_seen_at') as string),
  },
  // ...
]
```

Para listas grandes (events list >500 rows): usar `useVirtualizer` de
Tanstack Virtual directamente (ver patron en
`.claude/docs/admin/03-ui.md`).

## Forms con react-hook-form + Zod + shadcn — patron

Ver `.claude/docs/admin/03-ui.md` para LoginForm completo. Reglas:

- **SIEMPRE** Zod schema en `lib/validation/<feature>.ts`.
- **SIEMPRE** `zodResolver(schema)` en `useForm`.
- **SIEMPRE** shadcn `<Form>`, `<FormField>`, `<FormControl>`,
  `<FormMessage>`.
- **SIEMPRE** mostrar errores del mutation con `<Alert variant="destructive">`
  o `toast.error()`.

## Loading states

- **SIEMPRE** `<Skeleton>` realistic (forma del componente final) sobre
  spinner generico.
- **SIEMPRE** todo Suspense boundary tiene fallback (loading.tsx en App
  Router o Skeleton inline).

## Empty states

- **SIEMPRE** `<EmptyState>` cuando no hay data. Icon + title +
  description corta + action button (recargar / cambiar filtro).

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| `useEffect(() => fetch(...))` en componente | Sin cache, sin retry, sin invalidation | Mover a hook con `useQuery` |
| `<PrimaryButton>` wrappeando `<Button variant="primary">` | Sin valor | `<Button variant="primary">` directo |
| Importar `@radix-ui/react-X` directo | Pierde theming | Pasar por `@/components/ui/X` |
| Recharts `fill="#FF0000"` | Rompe dark/light | `fill="hsl(var(--primary))"` |
| Spinner generico mientras carga MetricCard | Mala UX | Skeleton con forma de Card |
| Mostrar mensaje "Error" sin retry | Dead-end | `<ErrorAlert error onRetry />` |
| Form con `onChange` manual + state local | Boilerplate | react-hook-form + Zod |
| Tabla sin sort/paginator | Mala UX en >50 rows | DataTable wrapper o feature-specific |

[< 04-setup-base](04-setup-base.md) | [Siguiente: 06-auth-feature >](06-auth-feature.md)
