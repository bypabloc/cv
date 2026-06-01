'use client'

import { CalendarIcon } from 'lucide-react'
import type { DateRange } from 'react-day-picker'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { cn } from '@/lib/utils'

/**
 * @component DateRangePicker
 * @description Popover + Calendar para seleccionar un rango de fechas.
 *   Controlado: el caller mantiene el `value` y recibe `onChange`.
 *
 * @props {DateRange | undefined} value - rango seleccionado
 * @props {(range: DateRange | undefined) => void} onChange - callback
 * @props {string} [className] - clases extra del trigger
 */
export function DateRangePicker({
  value,
  onChange,
  className,
}: {
  value: DateRange | undefined
  onChange: (range: DateRange | undefined) => void
  className?: string
}) {
  const label =
    value?.from && value?.to
      ? `${value.from.toLocaleDateString('es')} - ${value.to.toLocaleDateString('es')}`
      : 'Elegir rango'

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn('justify-start text-left font-normal', className)}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {label}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="range"
          selected={value}
          onSelect={onChange}
          numberOfMonths={2}
          autoFocus
        />
      </PopoverContent>
    </Popover>
  )
}
