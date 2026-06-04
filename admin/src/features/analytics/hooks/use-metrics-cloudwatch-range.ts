"use client";

import { useState } from "react";
import { type ResolvedRange, resolveRelative } from "../lib/range-presets";

/**
 * @function useMetricsCloudwatchRange
 * @description Estado del rango de la page raiz /metrics: from/to datetime ISO
 *   (UTC) + bucket derivado. Lo produce el selector CloudWatch
 *   (MetricsRangePicker). Default: ultimos 30 dias (bucket day). A diferencia
 *   de useMetricsRange (sub-pages, YYYY-MM-DD), este soporta granularidad
 *   sub-dia para los presets cortos (5m/1h/...).
 *
 * @returns `{ range, setRange }` donde range es `{from, to, bucket}`.
 */
export function useMetricsCloudwatchRange(): {
	range: ResolvedRange;
	setRange: (range: ResolvedRange) => void;
} {
	const [range, setRange] = useState<ResolvedRange>(() =>
		resolveRelative(30, "days"),
	);
	return { range, setRange };
}
