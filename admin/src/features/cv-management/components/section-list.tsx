"use client";

import {
	ArrowDown,
	ArrowUp,
	FileText,
	Pencil,
	Plus,
	Trash2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import type { SectionListItem } from "../lib/sections";

/**
 * @component SectionList
 * @description Lista de cards de una seccion del CV: selector de niche
 *   activo (define el orden mostrado y habilita el reorden), botones
 *   subir/bajar por card (emiten la lista COMPLETA resultante de slugs),
 *   editar/eliminar por card, boton de alta, empty state y skeletons.
 *
 * @props {SectionListItem[]} items - Items normalizados (toListItem)
 * @props {boolean} isLoading - Query en vuelo (skeletons)
 * @props {string[]} niches - Catalogo de niches para el selector
 * @props {string} activeNiche - Niche activo ('' = todos, sin reorden)
 * @props {(niche: string) => void} onNicheChange
 * @props {() => void} onNew - Abrir alta
 * @props {(slug: string) => void} onEdit - Abrir edicion
 * @props {(slug: string) => void} onDelete - Abrir confirmacion de borrado
 * @props {(orderedSlugs: string[]) => void} onReorder - Orden nuevo completo
 */
interface SectionListProps {
	items: SectionListItem[];
	isLoading: boolean;
	niches: string[];
	activeNiche: string;
	onNicheChange: (niche: string) => void;
	onNew: () => void;
	onEdit: (slug: string) => void;
	onDelete: (slug: string) => void;
	onReorder: (orderedSlugs: string[]) => void;
}

/** Sentinela del selector: '' no es un value valido de Radix Select. */
const ALL_NICHES = "_all";

function reordered(items: SectionListItem[], from: number, to: number) {
	const slugs = items.map((item) => item.slug);
	const moved = slugs[from];
	const swapped = slugs[to];
	if (moved === undefined || swapped === undefined) return null;
	slugs[from] = swapped;
	slugs[to] = moved;
	return slugs;
}

export function SectionList({
	items,
	isLoading,
	niches,
	activeNiche,
	onNicheChange,
	onNew,
	onEdit,
	onDelete,
	onReorder,
}: SectionListProps) {
	const reorderEnabled = activeNiche !== "";

	const move = (index: number, delta: -1 | 1): void => {
		const next = reordered(items, index, index + delta);
		if (next) onReorder(next);
	};

	return (
		<div className="space-y-4">
			<div className="flex flex-wrap items-center justify-between gap-2">
				<Select
					value={activeNiche === "" ? ALL_NICHES : activeNiche}
					onValueChange={(value) =>
						onNicheChange(value === ALL_NICHES ? "" : value)
					}
				>
					<SelectTrigger className="w-44" data-testid="cv-niche-select">
						<SelectValue placeholder="Todos los niches" />
					</SelectTrigger>
					<SelectContent>
						<SelectItem value={ALL_NICHES}>Todos los niches</SelectItem>
						{niches.map((niche) => (
							<SelectItem key={niche} value={niche}>
								{niche}
							</SelectItem>
						))}
					</SelectContent>
				</Select>
				<Button type="button" data-testid="cv-entity-new" onClick={onNew}>
					<Plus className="h-4 w-4" /> Nueva entrada
				</Button>
			</div>

			{isLoading ? (
				<div className="space-y-2" data-testid="cv-section-skeleton">
					<Skeleton className="h-20 w-full" />
					<Skeleton className="h-20 w-full" />
					<Skeleton className="h-20 w-full" />
				</div>
			) : items.length === 0 ? (
				<EmptyState
					icon={FileText}
					title="Sin entradas"
					description="Crea la primera entrada de esta seccion."
				/>
			) : (
				<ul className="space-y-2">
					{items.map((item, index) => (
						<li key={item.slug}>
							<Card data-testid="cv-entity-card" data-slug={item.slug}>
								<CardContent className="flex items-center justify-between gap-3 py-4">
									<div className="min-w-0 space-y-1">
										<p className="truncate font-medium">{item.title}</p>
										<p className="truncate text-sm text-muted-foreground">
											{item.subtitle}
										</p>
										<div className="flex flex-wrap gap-1">
											{item.niches.map((niche) => (
												<Badge key={niche} variant="outline">
													{niche}
												</Badge>
											))}
										</div>
									</div>
									<div className="flex shrink-0 gap-1">
										{reorderEnabled ? (
											<>
												<Button
													type="button"
													variant="ghost"
													size="icon"
													data-testid="cv-entity-move-up"
													aria-label={`Subir ${item.slug}`}
													disabled={index === 0}
													onClick={() => move(index, -1)}
												>
													<ArrowUp className="h-4 w-4" />
												</Button>
												<Button
													type="button"
													variant="ghost"
													size="icon"
													data-testid="cv-entity-move-down"
													aria-label={`Bajar ${item.slug}`}
													disabled={index === items.length - 1}
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
											data-testid="cv-entity-edit"
											aria-label={`Editar ${item.slug}`}
											onClick={() => onEdit(item.slug)}
										>
											<Pencil className="h-4 w-4" />
										</Button>
										<Button
											type="button"
											variant="ghost"
											size="icon"
											data-testid="cv-entity-delete"
											aria-label={`Eliminar ${item.slug}`}
											onClick={() => onDelete(item.slug)}
										>
											<Trash2 className="h-4 w-4" />
										</Button>
									</div>
								</CardContent>
							</Card>
						</li>
					))}
				</ul>
			)}
		</div>
	);
}
