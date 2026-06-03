/**
 * @module features/devices/types
 * @description Shapes de las respuestas de la operation `devices` del Lambda
 *   `analytics`: breakdown (distribucion por tipo de dispositivo, navegador y
 *   sistema operativo). Espejan el `data` que devuelve cada endpoint.
 */

/** Rango de fechas compartido por los endpoints de metricas. */
export interface DateRangeParams {
	from?: string;
	to?: string;
}

/** Una fila de distribucion por tipo de dispositivo. */
export interface DeviceTypeDist {
	device_type: string;
	sessions: number;
}

/** Una fila de distribucion por navegador. */
export interface BrowserDist {
	browser: string;
	sessions: number;
}

/** Una fila de distribucion por sistema operativo. */
export interface OsDist {
	os: string;
	sessions: number;
}

/** devices/breakdown — 3 distribuciones de sesiones. */
export interface BreakdownResponse {
	device_types: DeviceTypeDist[];
	browsers: BrowserDist[];
	os: OsDist[];
}

export type BreakdownParams = DateRangeParams;
