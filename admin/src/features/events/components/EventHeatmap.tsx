"use client";

import { Skeleton } from "@/components/ui/skeleton";
import type { HeatmapResponse } from "../types";

/**
 * @component EventHeatmap
 * @description Grilla 7x24 (dias de semana x horas) de eventos (events/heatmap).
 *   Filas = dias (Lun..Dom, ISO 1-7), columnas = horas 0-23. Cada celda se
 *   colorea con opacidad proporcional a su `count` (mas eventos = mas opaco)
 *   usando `--primary`. Skeleton mientras carga; mensaje si vacio.
 *
 * @props {HeatmapResponse} [data] - celdas del backend
 * @props {boolean} isLoading - estado de carga
 */
const DAY_LABELS = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"] as const;
const HOURS = Array.from({ length: 24 }, (_, h) => h);

export function EventHeatmap({
	data,
	isLoading,
}: {
	data?: HeatmapResponse;
	isLoading: boolean;
}) {
	if (isLoading || !data) {
		return <Skeleton className="h-72 w-full" />;
	}
	if (data.cells.length === 0) {
		return (
			<div className="flex h-72 items-center justify-center text-sm text-muted-foreground">
				Sin eventos en el rango seleccionado.
			</div>
		);
	}

	// Indexa las celdas por (dow, hour) para lookup O(1) + calcula el maximo
	// para normalizar la intensidad.
	const counts = new Map<string, number>();
	let max = 0;
	for (const cell of data.cells) {
		counts.set(`${cell.dow}-${cell.hour}`, cell.count);
		if (cell.count > max) max = cell.count;
	}

	function intensity(count: number): number {
		if (max === 0 || count === 0) return 0;
		// Minimo 0.12 para que una celda con datos sea visible, hasta 1.
		return 0.12 + 0.88 * (count / max);
	}

	return (
		<div className="overflow-x-auto">
			<div className="inline-block min-w-full">
				<div className="flex">
					<div className="w-10 shrink-0" />
					{HOURS.map((hour) => (
						<div
							key={`head-${hour}`}
							className="w-6 shrink-0 text-center text-[10px] text-muted-foreground"
						>
							{hour % 3 === 0 ? hour : ""}
						</div>
					))}
				</div>
				{DAY_LABELS.map((label, idx) => {
					const dow = idx + 1;
					return (
						<div key={label} className="flex items-center">
							<div className="w-10 shrink-0 pr-2 text-right text-xs text-muted-foreground">
								{label}
							</div>
							{HOURS.map((hour) => {
								const count = counts.get(`${dow}-${hour}`) ?? 0;
								return (
									<div
										key={`${dow}-${hour}`}
										title={`${label} ${String(hour).padStart(2, "0")}:00 — ${count} eventos`}
										className="m-px h-6 w-6 shrink-0 rounded-sm border border-border/40"
										style={{
											backgroundColor: "var(--primary)",
											opacity: intensity(count),
										}}
									/>
								);
							})}
						</div>
					);
				})}
			</div>
		</div>
	);
}
