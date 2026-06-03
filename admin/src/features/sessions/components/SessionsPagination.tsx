"use client";

import { Button } from "@/components/ui/button";

/**
 * @component SessionsPagination
 * @description Controles de paginacion del listado de sesiones: "Anterior" /
 *   "Siguiente" + el rango mostrado (page/total). El boton siguiente se
 *   deshabilita cuando `has_more` es false; el anterior cuando `page <= 1`.
 *
 * @props {number} page - pagina actual (1-based)
 * @props {number} pageSize - tamano de pagina
 * @props {number} total - total de sesiones
 * @props {boolean} hasMore - hay mas paginas despues de la actual
 * @props {boolean} isLoading - deshabilita los botones mientras carga
 * @props {(page: number) => void} onPageChange - cambia de pagina
 */
export function SessionsPagination({
	page,
	pageSize,
	total,
	hasMore,
	isLoading,
	onPageChange,
}: {
	page: number;
	pageSize: number;
	total: number;
	hasMore: boolean;
	isLoading: boolean;
	onPageChange: (page: number) => void;
}) {
	const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
	const to = Math.min(page * pageSize, total);

	return (
		<div className="flex items-center justify-between gap-3">
			<p className="text-sm text-muted-foreground">
				{from}-{to} de {total}
			</p>
			<div className="flex items-center gap-2">
				<Button
					variant="outline"
					size="sm"
					disabled={page <= 1 || isLoading}
					onClick={() => onPageChange(page - 1)}
				>
					Anterior
				</Button>
				<Button
					variant="outline"
					size="sm"
					disabled={!hasMore || isLoading}
					onClick={() => onPageChange(page + 1)}
				>
					Siguiente
				</Button>
			</div>
		</div>
	);
}
