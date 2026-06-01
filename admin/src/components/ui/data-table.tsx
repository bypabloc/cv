"use client";

import {
	type ColumnDef,
	flexRender,
	getCoreRowModel,
	getSortedRowModel,
	type SortingState,
	useReactTable,
} from "@tanstack/react-table";
import { useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";

/**
 * @component DataTable
 * @description Wrapper generico de Tanstack Table v8: render de columnas +
 *   sorting client-side + estados loading (skeleton) y empty.
 *
 * @props {ColumnDef<TData, TValue>[]} columns - definicion de columnas
 * @props {TData[]} data - filas
 * @props {boolean} [isLoading] - muestra skeleton rows
 * @props {string} [emptyMessage] - texto cuando no hay filas
 * @props {(row: TData) => void} [onRowClick] - click handler por fila
 */
export function DataTable<TData, TValue>({
	columns,
	data,
	isLoading = false,
	emptyMessage = "Sin resultados",
	onRowClick,
}: {
	columns: ColumnDef<TData, TValue>[];
	data: TData[];
	isLoading?: boolean;
	emptyMessage?: string;
	onRowClick?: (row: TData) => void;
}) {
	const [sorting, setSorting] = useState<SortingState>([]);
	const table = useReactTable({
		data,
		columns,
		state: { sorting },
		onSortingChange: setSorting,
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
	});

	return (
		<div className="rounded-md border">
			<Table>
				<TableHeader>
					{table.getHeaderGroups().map((headerGroup) => (
						<TableRow key={headerGroup.id}>
							{headerGroup.headers.map((header) => (
								<TableHead key={header.id}>
									{header.isPlaceholder
										? null
										: flexRender(
												header.column.columnDef.header,
												header.getContext(),
											)}
								</TableHead>
							))}
						</TableRow>
					))}
				</TableHeader>
				<TableBody>
					{isLoading ? (
						Array.from({ length: 5 }).map((_, i) => (
							// biome-ignore lint/suspicious/noArrayIndexKey: skeleton placeholder
							<TableRow key={`skeleton-${i}`}>
								{columns.map((_col, ci) => (
									// biome-ignore lint/suspicious/noArrayIndexKey: skeleton placeholder
									<TableCell key={`skeleton-cell-${ci}`}>
										<Skeleton className="h-5 w-full" />
									</TableCell>
								))}
							</TableRow>
						))
					) : table.getRowModel().rows.length ? (
						table.getRowModel().rows.map((row) => (
							<TableRow
								key={row.id}
								data-state={row.getIsSelected() && "selected"}
								onClick={
									onRowClick ? () => onRowClick(row.original) : undefined
								}
								className={onRowClick ? "cursor-pointer" : undefined}
							>
								{row.getVisibleCells().map((cell) => (
									<TableCell key={cell.id}>
										{flexRender(cell.column.columnDef.cell, cell.getContext())}
									</TableCell>
								))}
							</TableRow>
						))
					) : (
						<TableRow>
							<TableCell
								colSpan={columns.length}
								className="h-24 text-center text-muted-foreground"
							>
								{emptyMessage}
							</TableCell>
						</TableRow>
					)}
				</TableBody>
			</Table>
		</div>
	);
}
