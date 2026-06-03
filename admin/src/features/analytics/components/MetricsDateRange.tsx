"use client";

import type { DateRange } from "react-day-picker";
import { DateRangePicker } from "@/components/ui/date-range-picker";
import type { DateRangeParams } from "../types";

/**
 * @component MetricsDateRange
 * @description Wrapper del DateRangePicker para el rango de metricas: adapta
 *   entre los strings `YYYY-MM-DD` (params del backend) y los `Date` que usa
 *   el picker (react-day-picker). Al elegir un rango completo, lo propaga como
 *   `{from, to}` strings.
 *
 * @props {DateRangeParams} range - rango actual (from/to YYYY-MM-DD)
 * @props {(range: DateRangeParams) => void} onChange - callback con strings
 */
function toDate(s?: string): Date | undefined {
	if (!s) return undefined;
	const d = new Date(`${s}T00:00:00`);
	return Number.isNaN(d.getTime()) ? undefined : d;
}

function toIso(d?: Date): string | undefined {
	if (!d) return undefined;
	return d.toISOString().slice(0, 10);
}

export function MetricsDateRange({
	range,
	onChange,
}: {
	range: DateRangeParams;
	onChange: (range: DateRangeParams) => void;
}) {
	const value: DateRange | undefined = range.from
		? { from: toDate(range.from), to: toDate(range.to) }
		: undefined;

	return (
		<DateRangePicker
			value={value}
			onChange={(next) => {
				if (next?.from && next?.to) {
					onChange({ from: toIso(next.from), to: toIso(next.to) });
				}
			}}
		/>
	);
}
