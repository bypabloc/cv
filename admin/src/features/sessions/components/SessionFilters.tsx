"use client";

import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";

/**
 * @component SessionFilters
 * @description Filtros opcionales del listado de sesiones: device_type y
 *   browser. El valor `_all` representa "sin filtro" (se traduce a undefined
 *   en la page para no enviar el param).
 *
 * @props {string} [deviceType] - filtro de device_type activo
 * @props {string} [browser] - filtro de browser activo
 * @props {(value?: string) => void} onDeviceTypeChange - cambia device_type
 * @props {(value?: string) => void} onBrowserChange - cambia browser
 */
const ALL = "_all";

const DEVICE_TYPES: readonly string[] = ["desktop", "mobile", "tablet", "bot"];

const BROWSERS: readonly string[] = [
	"Chrome",
	"Firefox",
	"Safari",
	"Edge",
	"Opera",
];

export function SessionFilters({
	deviceType,
	browser,
	onDeviceTypeChange,
	onBrowserChange,
}: {
	deviceType?: string;
	browser?: string;
	onDeviceTypeChange: (value?: string) => void;
	onBrowserChange: (value?: string) => void;
}) {
	return (
		<div className="flex flex-wrap items-center gap-3">
			<Select
				value={deviceType ?? ALL}
				onValueChange={(v) => onDeviceTypeChange(v === ALL ? undefined : v)}
			>
				<SelectTrigger className="w-40">
					<SelectValue placeholder="Dispositivo" />
				</SelectTrigger>
				<SelectContent>
					<SelectItem value={ALL}>Todos los dispositivos</SelectItem>
					{DEVICE_TYPES.map((type) => (
						<SelectItem key={type} value={type}>
							{type}
						</SelectItem>
					))}
				</SelectContent>
			</Select>

			<Select
				value={browser ?? ALL}
				onValueChange={(v) => onBrowserChange(v === ALL ? undefined : v)}
			>
				<SelectTrigger className="w-40">
					<SelectValue placeholder="Navegador" />
				</SelectTrigger>
				<SelectContent>
					<SelectItem value={ALL}>Todos los navegadores</SelectItem>
					{BROWSERS.map((b) => (
						<SelectItem key={b} value={b}>
							{b}
						</SelectItem>
					))}
				</SelectContent>
			</Select>
		</div>
	);
}
