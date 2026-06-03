"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import type { ContactByStatusResponse } from "../types";

/**
 * @component ContactByStatusChart
 * @description Desglose de contactos por estado (contacts/by-status) como
 *   PieChart de Recharts. Colores via CSS vars del DS. Skeleton mientras
 *   carga; mensaje si vacio.
 *
 * @props {ContactByStatusResponse} [data] - desglose del backend
 * @props {boolean} isLoading - estado de carga
 */
const SLICE_COLORS: readonly string[] = [
	"var(--primary)",
	"var(--muted-foreground)",
	"var(--chart-3, var(--secondary))",
	"var(--chart-4, var(--accent))",
	"var(--destructive)",
];

export function ContactByStatusChart({
	data,
	isLoading,
}: {
	data?: ContactByStatusResponse;
	isLoading: boolean;
}) {
	if (isLoading || !data) {
		return <Skeleton className="h-64 w-full" />;
	}
	if (data.items.length === 0) {
		return (
			<div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
				Sin contactos en el rango seleccionado.
			</div>
		);
	}

	return (
		<ResponsiveContainer width="100%" height={256}>
			<PieChart>
				<Pie
					data={data.items}
					dataKey="count"
					nameKey="status"
					innerRadius={50}
					outerRadius={88}
					paddingAngle={2}
				>
					{data.items.map((item, i) => (
						<Cell
							key={item.status}
							fill={SLICE_COLORS[i % SLICE_COLORS.length]}
						/>
					))}
				</Pie>
				<Tooltip
					contentStyle={{
						background: "var(--popover)",
						border: "1px solid var(--border)",
						borderRadius: 8,
						fontSize: 12,
					}}
				/>
			</PieChart>
		</ResponsiveContainer>
	);
}
