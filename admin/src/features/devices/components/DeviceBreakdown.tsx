"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BreakdownResponse } from "../types";
import { DistributionChart } from "./DistributionChart";

/**
 * @component DeviceBreakdown
 * @description Las 3 distribuciones de devices/breakdown (tipos de dispositivo,
 *   navegadores, sistemas operativos) como BarCharts lado a lado, cada uno en
 *   su Card. Ordenado desc por sessions dentro de cada chart.
 *
 * @props {BreakdownResponse} [data] - distribuciones del backend
 * @props {boolean} isLoading - estado de carga
 */
export function DeviceBreakdown({
	data,
	isLoading,
}: {
	data?: BreakdownResponse;
	isLoading: boolean;
}) {
	return (
		<div className="grid gap-6 lg:grid-cols-3">
			<Card>
				<CardHeader>
					<CardTitle>Tipos de dispositivo</CardTitle>
				</CardHeader>
				<CardContent>
					<DistributionChart
						data={data?.device_types}
						nameKey="device_type"
						isLoading={isLoading}
					/>
				</CardContent>
			</Card>

			<Card>
				<CardHeader>
					<CardTitle>Navegadores</CardTitle>
				</CardHeader>
				<CardContent>
					<DistributionChart
						data={data?.browsers}
						nameKey="browser"
						isLoading={isLoading}
					/>
				</CardContent>
			</Card>

			<Card>
				<CardHeader>
					<CardTitle>Sistemas operativos</CardTitle>
				</CardHeader>
				<CardContent>
					<DistributionChart
						data={data?.os}
						nameKey="os"
						isLoading={isLoading}
					/>
				</CardContent>
			</Card>
		</div>
	);
}
