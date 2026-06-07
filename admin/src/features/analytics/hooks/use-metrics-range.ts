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
 * @description Estado del rango de fechas (YYYY-MM-DD) que comparten las
 *   SUB-pages de metricas (devices, funnel, events, ...). Default: ultimos 30
 *   dias. La page raiz /metrics usa su propio selector CloudWatch
 *   (useMetricsCloudwatchRange) con granularidad sub-dia + bucket.
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
