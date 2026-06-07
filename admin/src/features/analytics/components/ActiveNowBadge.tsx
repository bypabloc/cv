"use client";

import { Radio } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useActiveNow } from "../hooks/use-active-now";

/**
 * @component ActiveNowBadge
 * @description Contador live de sesiones activas (analytics/active-now). Punto
 *   verde pulsante + conteo. Mientras carga o si falla, muestra un guion sin
 *   romper el layout.
 *
 *   Dos modos:
 *   - `standalone` (default): dispara su propia query `useActiveNow` (refetch
 *     15s). Uso suelto del badge fuera de /metrics.
 *   - `standalone={false}`: NO consulta — la page /metrics ya recibe active-now
 *     en el payload de `analytics/dashboard` y lo pasa via `count`. Asi el
 *     badge no agrega una request extra al fan-out unificado.
 *
 * @props {number} [count] - sesiones activas (del dashboard). Si es undefined
 *   muestra el guion.
 * @props {boolean} [standalone] - si dispara su propia query (default true).
 */
export function ActiveNowBadge({
	count: countProp,
	standalone = true,
}: {
	count?: number;
	standalone?: boolean;
} = {}) {
	const { data, isLoading, isError } = useActiveNow({ enabled: standalone });
	const liveCount = isLoading || isError || !data ? "–" : data.active_sessions;
	const count = standalone ? liveCount : (countProp ?? "–");

	return (
		<Badge variant="secondary" className="gap-2">
			<span className="relative flex h-2 w-2">
				<span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-500 opacity-75" />
				<span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
			</span>
			<Radio className="h-3.5 w-3.5" />
			<span>
				{count}{" "}
				{typeof count === "number" && count === 1 ? "activo" : "activos"}
			</span>
		</Badge>
	);
}
