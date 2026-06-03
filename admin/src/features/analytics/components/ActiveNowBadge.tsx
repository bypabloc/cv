"use client";

import { Radio } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useActiveNow } from "../hooks/use-active-now";

/**
 * @component ActiveNowBadge
 * @description Contador live de sesiones activas (analytics/active-now), con
 *   refetch cada 15s. Punto verde pulsante + conteo. Si falla o carga, muestra
 *   un guion sin romper el layout.
 */
export function ActiveNowBadge() {
	const { data, isLoading, isError } = useActiveNow();
	const count = isLoading || isError || !data ? "–" : data.active_sessions;

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
