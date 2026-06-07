"use client";

import type { LucideIcon } from "lucide-react";
import { Mail, MousePointerClick, Users } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import type { FunnelConversionResponse } from "../types";

/**
 * @component FunnelChart
 * @description Embudo visual de conversion (funnel/conversion): 3 barras
 *   horizontales decrecientes (sessions -> visits -> contacts) con el width
 *   proporcional al numero de sesiones (etapa raiz). Entre etapas muestra la
 *   tasa de conversion formateada como porcentaje. Skeleton mientras carga;
 *   mensaje si no hay sesiones en el rango.
 *
 * @props {FunnelConversionResponse} [data] - embudo del backend
 * @props {boolean} isLoading - estado de carga
 */
interface StageDef {
	key: "sessions" | "visits" | "contacts";
	label: string;
	icon: LucideIcon;
}

const STAGES: readonly StageDef[] = [
	{ key: "sessions", label: "Sesiones", icon: Users },
	{ key: "visits", label: "Visitas", icon: MousePointerClick },
	{ key: "contacts", label: "Contactos", icon: Mail },
];

function fmtInt(v: number): string {
	return new Intl.NumberFormat("es").format(Math.round(v));
}

function fmtPct(v: number): string {
	return `${(v * 100).toFixed(1)}%`;
}

export function FunnelChart({
	data,
	isLoading,
}: {
	data?: FunnelConversionResponse;
	isLoading: boolean;
}) {
	if (isLoading || !data) {
		return (
			<div className="space-y-4">
				<Skeleton className="h-12 w-full" />
				<Skeleton className="h-12 w-3/4" />
				<Skeleton className="h-12 w-1/2" />
			</div>
		);
	}

	if (data.sessions === 0) {
		return (
			<p className="py-6 text-center text-sm text-muted-foreground">
				Sin sesiones en el rango seleccionado.
			</p>
		);
	}

	const stageRates: Record<string, number> = {
		visits: data.session_to_visit_rate,
		contacts: data.visit_to_contact_rate,
	};

	return (
		<div className="space-y-2">
			{STAGES.map((stage, index) => {
				const Icon = stage.icon;
				const value = data[stage.key];
				const width = data.sessions > 0 ? (value / data.sessions) * 100 : 0;
				return (
					<div key={stage.key} className="space-y-2">
						{index > 0 ? (
							<p className="text-center text-xs text-muted-foreground">
								{fmtPct(stageRates[stage.key] ?? 0)} de conversion
							</p>
						) : null}
						<div
							className="flex h-12 items-center justify-between rounded-md bg-primary px-4 text-primary-foreground"
							style={{ width: `${Math.max(width, 18)}%` }}
						>
							<span className="flex items-center gap-2 text-sm font-medium">
								<Icon className="h-4 w-4" />
								{stage.label}
							</span>
							<span className="text-sm font-semibold tabular-nums">
								{fmtInt(value)}
							</span>
						</div>
					</div>
				);
			})}
			<p className="pt-2 text-center text-xs text-muted-foreground">
				Conversion total (sesion a contacto):{" "}
				<span className="font-medium text-foreground">
					{fmtPct(data.session_to_contact_rate)}
				</span>
			</p>
		</div>
	);
}
