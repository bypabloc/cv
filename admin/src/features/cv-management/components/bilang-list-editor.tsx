"use client";

import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/**
 * @component BiLangListEditor
 * @description Editor de listas paralelas es/en (bullets de experiencia):
 *   cada fila es un par es|en con eliminar/subir/bajar, mas un boton de
 *   agregar. Mantiene ids internos estables por fila (keys sin indice) y
 *   proyecta `{es: string[], en: string[]}` hacia el form en cada cambio.
 *   El valor inicial se toma UNA vez al montar (el dialog re-monta por
 *   entidad via key), el estado vive adentro.
 *
 * @props {string} name - Identificador (data-testid del bloque)
 * @props {string} label - Label del editor
 * @props {{es: string[], en: string[]}} value - Listas iniciales paralelas
 * @props {(next: {es: string[], en: string[]}) => void} onChange - Proyeccion
 * @props {string} [error] - Mensaje de error del schema
 */
interface BiLangListEditorProps {
	name: string;
	label: string;
	value: { es: string[]; en: string[] };
	onChange: (next: { es: string[]; en: string[] }) => void;
	error?: string;
}

interface Row {
	id: number;
	es: string;
	en: string;
}

function toRows(value: { es: string[]; en: string[] }): Row[] {
	const total = Math.max(value.es.length, value.en.length);
	return Array.from({ length: total }, (_, position) => ({
		id: position,
		es: value.es[position] ?? "",
		en: value.en[position] ?? "",
	}));
}

function project(rows: Row[]): { es: string[]; en: string[] } {
	return { es: rows.map((row) => row.es), en: rows.map((row) => row.en) };
}

function swap(rows: Row[], from: number, to: number): Row[] {
	const next = [...rows];
	const moved = next[from];
	const target = next[to];
	if (moved === undefined || target === undefined) return rows;
	next[from] = target;
	next[to] = moved;
	return next;
}

export function BiLangListEditor({
	name,
	label,
	value,
	onChange,
	error,
}: BiLangListEditorProps) {
	const [rows, setRows] = useState<Row[]>(() => toRows(value));
	const nextIdRef = useRef(rows.length);

	const update = (next: Row[]): void => {
		setRows(next);
		onChange(project(next));
	};

	const setText = (id: number, locale: "es" | "en", text: string): void => {
		update(
			rows.map((row) => (row.id === id ? { ...row, [locale]: text } : row)),
		);
	};

	const addRow = (): void => {
		nextIdRef.current += 1;
		update([...rows, { id: nextIdRef.current, es: "", en: "" }]);
	};

	const removeRow = (id: number): void => {
		update(rows.filter((row) => row.id !== id));
	};

	const move = (index: number, delta: -1 | 1): void => {
		update(swap(rows, index, index + delta));
	};

	return (
		<div className="space-y-2" data-testid={`bilang-list-${name}`}>
			<Label>{label}</Label>
			<ul className="space-y-2">
				{rows.map((row, index) => (
					<li
						key={row.id}
						data-testid="bilang-item-row"
						className="flex items-start gap-2"
					>
						<div className="grid flex-1 grid-cols-1 gap-2 sm:grid-cols-2">
							<Input
								data-testid="bilang-item-es"
								aria-label={`${label} es`}
								placeholder="es"
								value={row.es}
								onChange={(event) => setText(row.id, "es", event.target.value)}
							/>
							<Input
								data-testid="bilang-item-en"
								aria-label={`${label} en`}
								placeholder="en"
								value={row.en}
								onChange={(event) => setText(row.id, "en", event.target.value)}
							/>
						</div>
						<div className="flex gap-1">
							<Button
								type="button"
								variant="ghost"
								size="icon"
								data-testid="bilang-item-up"
								aria-label="Subir item"
								disabled={index === 0}
								onClick={() => move(index, -1)}
							>
								<ArrowUp className="h-4 w-4" />
							</Button>
							<Button
								type="button"
								variant="ghost"
								size="icon"
								data-testid="bilang-item-down"
								aria-label="Bajar item"
								disabled={index === rows.length - 1}
								onClick={() => move(index, 1)}
							>
								<ArrowDown className="h-4 w-4" />
							</Button>
							<Button
								type="button"
								variant="ghost"
								size="icon"
								data-testid="bilang-item-remove"
								aria-label="Eliminar item"
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
				data-testid="bilang-item-add"
				onClick={addRow}
			>
				<Plus className="h-4 w-4" /> Agregar item
			</Button>
			{error ? (
				<p className="text-sm text-destructive" role="alert">
					{error}
				</p>
			) : null}
		</div>
	);
}
