"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/**
 * @component NichePriorityPicker
 * @description Checkboxes de niches (catalogo) + input numerico de prioridad
 *   por niche marcado. Controlado: emite `{niches, priority}` en cada
 *   cambio. Marcar un niche le asigna prioridad 1 por defecto; desmarcarlo
 *   elimina su entrada del mapa.
 *
 * @props {string[]} niches - Catalogo de niches (orden de presentacion)
 * @props {string[]} selected - Niches marcados
 * @props {Record<string, number>} priority - Prioridad por niche marcado
 * @props {(next: {niches: string[], priority: Record<string, number>}) => void} onChange
 * @props {boolean} [showPriority] - Mostrar inputs de prioridad (default true)
 * @props {string} [error] - Mensaje de error del schema
 */
interface NichePriorityPickerProps {
	niches: string[];
	selected: string[];
	priority: Record<string, number>;
	onChange: (next: {
		niches: string[];
		priority: Record<string, number>;
	}) => void;
	showPriority?: boolean;
	error?: string;
}

const DEFAULT_PRIORITY = 1;

export function NichePriorityPicker({
	niches,
	selected,
	priority,
	onChange,
	showPriority = true,
	error,
}: NichePriorityPickerProps) {
	const toggle = (slug: string, checked: boolean): void => {
		if (checked) {
			onChange({
				niches: [...selected, slug],
				priority: showPriority
					? { ...priority, [slug]: priority[slug] ?? DEFAULT_PRIORITY }
					: priority,
			});
			return;
		}
		const nextPriority = { ...priority };
		delete nextPriority[slug];
		onChange({
			niches: selected.filter((current) => current !== slug),
			priority: nextPriority,
		});
	};

	const setPriority = (slug: string, raw: string): void => {
		const parsed = Number(raw);
		onChange({
			niches: selected,
			priority: { ...priority, [slug]: Number.isNaN(parsed) ? 0 : parsed },
		});
	};

	return (
		<div className="space-y-2" data-testid="niche-priority-picker">
			<Label>Niches</Label>
			<ul className="space-y-2">
				{niches.map((slug) => {
					const checked = selected.includes(slug);
					return (
						<li key={slug} className="flex items-center gap-3">
							<span className="flex items-center gap-2 text-sm">
								<Checkbox
									id={`niche-checkbox-${slug}`}
									data-testid={`niche-checkbox-${slug}`}
									aria-label={`Niche ${slug}`}
									checked={checked}
									onCheckedChange={(state) => toggle(slug, state === true)}
								/>
								<Label htmlFor={`niche-checkbox-${slug}`}>{slug}</Label>
							</span>
							{showPriority && checked ? (
								<Input
									type="number"
									className="h-8 w-24"
									data-testid={`niche-priority-${slug}`}
									aria-label={`Prioridad ${slug}`}
									value={priority[slug] ?? DEFAULT_PRIORITY}
									onChange={(event) => setPriority(slug, event.target.value)}
								/>
							) : null}
						</li>
					);
				})}
			</ul>
			{error ? (
				<p className="text-sm text-destructive" role="alert">
					{error}
				</p>
			) : null}
		</div>
	);
}
