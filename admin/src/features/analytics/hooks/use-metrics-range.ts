"use client";

import { useState } from "react";
import type { DateRangeParams } from "../types";

/**
 * @function isoDate
 * @description Formatea un Date a `YYYY-MM-DD` (UTC) para los params from/to.
 */
function isoDate(d: Date): string {
	return d.toISOString().slice(0, 10);
}

/**
 * @function useMetricsRange
 * @description Estado del rango de fechas compartido por las pages de metricas.
 *   Default: ultimos 30 dias (matchea el default del backend). El backend
 *   rechaza rangos > 90 dias (400); el DateRangePicker debe acotar a 90d.
 *
 * @returns `{ range, setRange }` donde range es `{from, to}` (YYYY-MM-DD).
 */
export function useMetricsRange(): {
	range: DateRangeParams;
	setRange: (range: DateRangeParams) => void;
} {
	const [range, setRange] = useState<DateRangeParams>(() => {
		const to = new Date();
		const from = new Date();
		from.setDate(from.getDate() - 30);
		return { from: isoDate(from), to: isoDate(to) };
	});
	return { range, setRange };
}
