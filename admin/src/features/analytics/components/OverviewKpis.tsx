"use client";

import type { LucideIcon } from "lucide-react";
import {
	Activity,
	Clock,
	Eye,
	Mail,
	MousePointerClick,
	TrendingDown,
	Users,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { OverviewResponse } from "../types";

/**
 * @component OverviewKpis
 * @description Grid de KPI cards de analytics/overview: sessions, visits,
 *   events, contacts, unique_visitors, avg_visit_duration_sec, bounce_rate.
 *   Muestra skeletons mientras carga.
 *
 * @props {OverviewResponse} [data] - KPIs del backend
 * @props {boolean} isLoading - estado de carga
 */
interface KpiDef {
	key: keyof OverviewResponse;
	label: string;
	icon: LucideIcon;
	format: (v: number) => string;
}

function fmtInt(v: number): string {
	return new Intl.NumberFormat("es").format(Math.round(v));
}

function fmtDuration(sec: number): string {
	const s = Math.round(sec);
	if (s < 60) return `${s}s`;
	const m = Math.floor(s / 60);
	if (m < 60) return `${m}m ${s % 60}s`;
	const h = Math.floor(m / 60);
	return `${h}h ${m % 60}m`;
}

function fmtPct(v: number): string {
	return `${(v * 100).toFixed(1)}%`;
}

const KPIS: readonly KpiDef[] = [
	{ key: "sessions", label: "Sesiones", icon: Users, format: fmtInt },
	{ key: "visits", label: "Visitas", icon: Eye, format: fmtInt },
	{ key: "events", label: "Eventos", icon: MousePointerClick, format: fmtInt },
	{ key: "contacts", label: "Contactos", icon: Mail, format: fmtInt },
	{
		key: "unique_visitors",
		label: "Visitantes unicos",
		icon: Activity,
		format: fmtInt,
	},
	{
		key: "avg_visit_duration_sec",
		label: "Duracion media",
		icon: Clock,
		format: fmtDuration,
	},
	{
		key: "bounce_rate",
		label: "Tasa de rebote",
		icon: TrendingDown,
		format: fmtPct,
	},
];

export function OverviewKpis({
	data,
	isLoading,
}: {
	data?: OverviewResponse;
	isLoading: boolean;
}) {
	return (
		<div className="grid grid-cols-2 gap-4 md:grid-cols-4">
			{KPIS.map((kpi) => {
				const Icon = kpi.icon;
				return (
					<Card key={kpi.key}>
						<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
							<CardTitle className="text-sm font-medium text-muted-foreground">
								{kpi.label}
							</CardTitle>
							<Icon className="h-4 w-4 text-muted-foreground" />
						</CardHeader>
						<CardContent>
							{isLoading || !data ? (
								<Skeleton className="h-7 w-20" />
							) : (
								<p className="text-2xl font-semibold">
									{kpi.format(data[kpi.key] as number)}
								</p>
							)}
						</CardContent>
					</Card>
				);
			})}
		</div>
	);
}
