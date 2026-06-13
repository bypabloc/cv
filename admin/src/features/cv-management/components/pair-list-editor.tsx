"use client";

import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/**
 * @component PairListEditor
 * @description Editor de listas de pares {key, value} ORDENADAS: links de
 *   proyecto (label/url) y metricas (key/value con reorden). Ids internos
 *   estables por fila; proyecta la lista al form en cada cambio. El valor
 *   inicial se toma una vez al montar (el dialog re-monta por entidad).
 *
 * @props {string} label - Label del bloque
 * @props {string} keyLabel - Placeholder de la columna key
 * @props {string} valueLabel - Placeholder de la columna value
 * @props {{key: string, value: string}[]} value - Pares iniciales
 * @props {(next: {key: string, value: string}[]) => void} onChange
 * @props {string} testIdPrefix - Prefijo de data-testid (cv-link | cv-metric)
 * @props {boolean} [reorderable] - Botones subir/bajar por fila
 * @props {string} [error] - Mensaje de error del schema
 */
interface Pair {
	key: string;
	value: string;
}

interface PairListEditorProps {
	label: string;
	keyLabel: string;
	valueLabel: string;
	value: Pair[];
	onChange: (next: Pair[]) => void;
	testIdPrefix: string;
	reorderable?: boolean;
	error?: string;
}

interface Row extends Pair {
	id: number;
}

export function PairListEditor({
	label,
	keyLabel,
	valueLabel,
	value,
	onChange,
	testIdPrefix,
	reorderable = false,
	error,
}: PairListEditorProps) {
	const [rows, setRows] = useState<Row[]>(() =>
		value.map((pair, position) => ({ id: position, ...pair })),
	);
	const nextIdRef = useRef(rows.length);

	const update = (next: Row[]): void => {
		setRows(next);
		onChange(
			next.map(({ key, value: pairValue }) => ({ key, value: pairValue })),
		);
	};

	const setField = (id: number, field: keyof Pair, text: string): void => {
		update(
			rows.map((row) => (row.id === id ? { ...row, [field]: text } : row)),
		);
	};

	const addRow = (): void => {
		nextIdRef.current += 1;
		update([...rows, { id: nextIdRef.current, key: "", value: "" }]);
	};

	const removeRow = (id: number): void => {
		update(rows.filter((row) => row.id !== id));
	};

	const move = (index: number, delta: -1 | 1): void => {
		const target = index + delta;
		const moved = rows[index];
		const swapped = rows[target];
		if (moved === undefined || swapped === undefined) return;
		const next = [...rows];
		next[index] = swapped;
		next[target] = moved;
		update(next);
	};

	return (
		<div className="space-y-2" data-testid={`${testIdPrefix}-list`}>
			<Label>{label}</Label>
			<ul className="space-y-2">
				{rows.map((row, index) => (
					<li
						key={row.id}
						data-testid={`${testIdPrefix}-row`}
						className="flex items-start gap-2"
					>
						<div className="grid flex-1 grid-cols-1 gap-2 sm:grid-cols-2">
							<Input
								data-testid={`${testIdPrefix}-key`}
								aria-label={keyLabel}
								placeholder={keyLabel}
								value={row.key}
								onChange={(event) =>
									setField(row.id, "key", event.target.value)
								}
							/>
							<Input
								data-testid={`${testIdPrefix}-value`}
								aria-label={valueLabel}
								placeholder={valueLabel}
								value={row.value}
								onChange={(event) =>
									setField(row.id, "value", event.target.value)
								}
							/>
						</div>
						<div className="flex gap-1">
							{reorderable ? (
								<>
									<Button
										type="button"
										variant="ghost"
										size="icon"
										data-testid={`${testIdPrefix}-up`}
										aria-label="Subir"
										disabled={index === 0}
										onClick={() => move(index, -1)}
									>
										<ArrowUp className="h-4 w-4" />
									</Button>
									<Button
										type="button"
										variant="ghost"
										size="icon"
										data-testid={`${testIdPrefix}-down`}
										aria-label="Bajar"
										disabled={index === rows.length - 1}
										onClick={() => move(index, 1)}
									>
										<ArrowDown className="h-4 w-4" />
									</Button>
								</>
							) : null}
							<Button
								type="button"
								variant="ghost"
								size="icon"
								data-testid={`${testIdPrefix}-remove`}
								aria-label="Eliminar"
								onClick={() => removeRow(row.id)}
							>
								<Trash2 className="h-4 w-4" />
							</Button>
						</div>
					</li>
				))}
			</ul>
			<Button
				type="button"
				variant="outline"
				size="sm"
				data-testid={`${testIdPrefix}-add`}
				onClick={addRow}
			>
				<Plus className="h-4 w-4" /> Agregar
			</Button>
			{error ? (
				<p className="text-sm text-destructive" role="alert">
					{error}
				</p>
			) : null}
		</div>
	);
}
