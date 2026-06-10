"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ROUTES } from "@/lib/routes";
import { useCvSection } from "../hooks/use-cv-section";
import { CV_SECTIONS, countEntries, SECTION_CONFIG } from "../lib/sections";
import type { CvSection } from "../types";
import { PublishCard } from "./publish-card";

/**
 * @component CvOverview
 * @description Overview de /cv: una card por seccion con el CONTEO de
 *   entradas (link a la sub-ruta) + la card de publicacion. Las secciones
 *   sin lectura publica (publications) muestran un guion.
 */
function SectionCard({ section }: { section: CvSection }) {
	const query = useCvSection<unknown>(section);
	const count = countEntries(section, query.data);

	return (
		<Link
			href={ROUTES.admin.cvSection(section)}
			data-testid={`cv-section-card-${section}`}
		>
			<Card className="transition-colors hover:bg-accent/50">
				<CardHeader>
					<CardTitle className="text-base">
						{SECTION_CONFIG[section].label}
					</CardTitle>
				</CardHeader>
				<CardContent>
					{query.isLoading ? (
						<Skeleton className="h-8 w-10" />
					) : (
						<p
							className="text-2xl font-semibold"
							data-testid={`cv-section-count-${section}`}
						>
							{count ?? "—"}
						</p>
					)}
				</CardContent>
			</Card>
		</Link>
	);
}

export function CvOverview() {
	return (
		<section className="space-y-6">
			<h1 className="text-2xl font-semibold">Gestion de CV</h1>
			<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{CV_SECTIONS.map((section) => (
					<SectionCard key={section} section={section} />
				))}
			</div>
			<PublishCard />
		</section>
	);
}
