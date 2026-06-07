import type { TimeseriesBucket } from "../types";

/**
 * @module features/analytics/lib/range-presets
 * @description Helpers del selector de rango estilo CloudWatch: convierte un
 *   preset relativo (5m, 1h, 7d, ...) o un rango absoluto en `{from, to,
 *   bucket}` donde from/to son datetime ISO (UTC) y bucket se deriva de la
 *   duracion para que la serie tenga una cardinalidad razonable.
 */

/** Unidad de tiempo de un preset relativo. */
export type RelativeUnit = "minutes" | "hours" | "days" | "weeks";

/** Rango resuelto que consume la page /metrics + el backend analytics. */
export interface ResolvedRange {
	from: string;
	to: string;
	bucket: TimeseriesBucket;
}

const MS = {
	minute: 60_000,
	hour: 3_600_000,
	day: 86_400_000,
	week: 604_800_000,
} as const;

/** Milisegundos de una unidad relativa. */
export function unitMs(unit: RelativeUnit): number {
	switch (unit) {
		case "minutes":
			return MS.minute;
		case "hours":
			return MS.hour;
		case "days":
			return MS.day;
		case "weeks":
			return MS.week;
	}
}

/**
 * @function bucketForSpan
 * @description Deriva el bucket de agrupacion segun la duracion del rango (ms),
 *   acotando la cardinalidad de la serie: <=2h minuto, <=2d hora, <=60d dia,
 *   resto semana. Coincide con los limites del backend (minute<=48h, hour<=31d).
 */
export function bucketForSpan(spanMs: number): TimeseriesBucket {
	if (spanMs <= 2 * MS.hour) return "minute";
	if (spanMs <= 2 * MS.day) return "hour";
	if (spanMs <= 60 * MS.day) return "day";
	return "week";
}

/**
 * @function resolveRelative
 * @description Rango relativo "ultimos N <unit>" terminando en `now`. Devuelve
 *   from/to ISO (UTC) + bucket derivado del span.
 *
 * @param amount - cantidad (>=1)
 * @param unit - unidad de tiempo
 * @param now - instante de referencia (default: ahora)
 */
export function resolveRelative(
	amount: number,
	unit: RelativeUnit,
	now: Date = new Date(),
): ResolvedRange {
	const spanMs = amount * unitMs(unit);
	const to = now;
	const from = new Date(to.getTime() - spanMs);
	return {
		from: from.toISOString(),
		to: to.toISOString(),
		bucket: bucketForSpan(spanMs),
	};
}

/**
 * @function resolveAbsolute
 * @description Rango absoluto entre dos instantes. Devuelve from/to ISO (UTC) +
 *   bucket derivado del span. Si from > to, los intercambia.
 */
export function resolveAbsolute(from: Date, to: Date): ResolvedRange {
	const [lo, hi] = from.getTime() <= to.getTime() ? [from, to] : [to, from];
	return {
		from: lo.toISOString(),
		to: hi.toISOString(),
		bucket: bucketForSpan(hi.getTime() - lo.getTime()),
	};
}

/** Preset rapido de la fila superior del dropdown (chips de la imagen). */
export interface QuickPreset {
	id: string;
	label: string;
	amount: number;
	unit: RelativeUnit;
}

/** Chips de la fila superior: 5m / 30m / 1h / 3h / 12h (Custom va aparte). */
export const QUICK_PRESETS: readonly QuickPreset[] = [
	{ id: "5m", label: "5m", amount: 5, unit: "minutes" },
	{ id: "30m", label: "30m", amount: 30, unit: "minutes" },
	{ id: "1h", label: "1h", amount: 1, unit: "hours" },
	{ id: "3h", label: "3h", amount: 3, unit: "hours" },
	{ id: "12h", label: "12h", amount: 12, unit: "hours" },
];

/** Opciones del grid Relative por unidad (replica la imagen de CloudWatch). */
export const RELATIVE_GRID: Record<RelativeUnit, readonly number[]> = {
	minutes: [5, 10, 15, 30, 45],
	hours: [1, 2, 3, 6, 8, 12],
	days: [1, 2, 3, 4, 5, 6],
	weeks: [1, 2, 3, 4],
};

/** Etiqueta corta del rango actual para el trigger del picker. */
export function formatRangeLabel(range: ResolvedRange): string {
	const fmt = (iso: string) =>
		new Date(iso).toLocaleString(undefined, {
			month: "short",
			day: "numeric",
			hour: "2-digit",
			minute: "2-digit",
		});
	return `${fmt(range.from)} - ${fmt(range.to)}`;
}

/** Parte fecha `YYYY-MM-DD` (UTC) de un Date. */
export function toDateInput(d: Date): string {
	return d.toISOString().slice(0, 10);
}

/** Parte hora `hh:mm:ss` (UTC) de un Date. */
export function toTimeInput(d: Date): string {
	return d.toISOString().slice(11, 19);
}

/**
 * @function combineDateTime
 * @description Combina los inputs `date` (YYYY-MM-DD) + `time` (hh:mm:ss) en un
 *   Date UTC. Devuelve null si la fecha esta vacia o el resultado es invalido.
 */
export function combineDateTime(date: string, time: string): Date | null {
	if (!date) return null;
	const parsed = new Date(`${date}T${time || "00:00:00"}Z`);
	return Number.isNaN(parsed.getTime()) ? null : parsed;
}

/**
 * @function handleDayPick
 * @description Aplica un dia elegido en el calendario a un setter de fecha
 *   (formato YYYY-MM-DD). Ignora `undefined` (deseleccion de react-day-picker).
 */
export function handleDayPick(
	day: Date | undefined,
	setDate: (value: string) => void,
): void {
	if (day) setDate(toDateInput(day));
}
