"use client";

import { ArrowDown, ArrowUp, Plus, X } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/**
 * @component TagInput
 * @description Chips con sugerencias del catalogo + crear nuevo. Filtra las
 *   sugerencias por el texto tipeado (excluyendo las ya elegidas); Enter o
 *   el boton agregan el texto libre como tag nuevo. Con `reorderable` cada
 *   chip trae subir/bajar (el orden es el de presentacion, ej. skills de
 *   una categoria).
 *
 * @props {string} name - Identificador (data-testid tag-input-<name>)
 * @props {string} label - Label del campo
 * @props {string[]} value - Tags elegidos (controlado)
 * @props {(next: string[]) => void} onChange - Cambio de la lista
 * @props {string[]} suggestions - Vocabulario del catalogo
 * @props {boolean} [reorderable] - Botones subir/bajar por chip
 * @props {string} [error] - Mensaje de error del schema
 */
interface TagInputProps {
	name: string;
	label: string;
	value: string[];
	onChange: (next: string[]) => void;
	suggestions: string[];
	reorderable?: boolean;
	error?: string;
}

const MAX_SUGGESTIONS = 8;

export function TagInput({
	name,
	label,
	value,
	onChange,
	suggestions,
	reorderable = false,
	error,
}: TagInputProps) {
	const [draft, setDraft] = useState("");

	const filtered =
		draft === ""
			? []
			: suggestions
					.filter(
						(suggestion) =>
							suggestion.toLowerCase().includes(draft.toLowerCase()) &&
							!value.includes(suggestion),
					)
					.slice(0, MAX_SUGGESTIONS);

	const add = (tag: string): void => {
		const trimmed = tag.trim();
		if (trimmed === "" || value.includes(trimmed)) return;
		onChange([...value, trimmed]);
		setDraft("");
	};

	const remove = (tag: string): void => {
		onChange(value.filter((current) => current !== tag));
	};

	const move = (index: number, delta: -1 | 1): void => {
		const target = index + delta;
		const moved = value[index];
		const swapped = value[target];
		if (moved === undefined || swapped === undefined) return;
		const next = [...value];
		next[index] = swapped;
		next[target] = moved;
		onChange(next);
	};

	return (
		<div className="space-y-2" data-testid={`tag-input-${name}`}>
			<Label>{label}</Label>
			<div className="flex flex-wrap gap-1.5">
				{value.map((tag, index) => (
					<Badge
						key={tag}
						variant="secondary"
						data-testid="tag-chip"
						data-value={tag}
						className="gap-1"
					>
						{tag}
						{reorderable ? (
							<>
								<button
									type="button"
									data-testid="tag-chip-up"
									aria-label={`Subir ${tag}`}
									disabled={index === 0}
									onClick={() => move(index, -1)}
								>
									<ArrowUp className="h-3 w-3" />
								</button>
								<button
									type="button"
									data-testid="tag-chip-down"
									aria-label={`Bajar ${tag}`}
									disabled={index === value.length - 1}
									onClick={() => move(index, 1)}
								>
									<ArrowDown className="h-3 w-3" />
								</button>
							</>
						) : null}
						<button
							type="button"
							data-testid="tag-chip-remove"
							aria-label={`Eliminar ${tag}`}
							onClick={() => remove(tag)}
						>
							<X className="h-3 w-3" />
						</button>
					</Badge>
				))}
			</div>
			<div className="flex gap-2">
				<Input
					data-testid={`tag-input-${name}-field`}
					aria-label={label}
					value={draft}
					placeholder="Escribe para buscar o crear"
					onChange={(event) => setDraft(event.target.value)}
					onKeyDown={(event) => {
						if (event.key === "Enter") {
							event.preventDefault();
							add(draft);
						}
					}}
				/>
				<Button
					type="button"
					variant="outline"
					size="sm"
					data-testid="tag-add"
					aria-label={`Agregar ${label}`}
					onClick={() => add(draft)}
				>
					<Plus className="h-4 w-4" />
				</Button>
			</div>
			{filtered.length > 0 ? (
				<ul className="flex flex-wrap gap-1.5">
					{filtered.map((suggestion) => (
						<li key={suggestion}>
							<button
								type="button"
								data-testid="tag-suggestion"
								data-value={suggestion}
								className="rounded-md border px-2 py-0.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
								onClick={() => add(suggestion)}
							>
								{suggestion}
							</button>
						</li>
					))}
				</ul>
			) : null}
			{error ? (
				<p className="text-sm text-destructive" role="alert">
					{error}
				</p>
			) : null}
		</div>
	);
}
