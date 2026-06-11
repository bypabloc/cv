"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ROUTES } from "@/lib/routes";
import { useFullCv } from "../hooks/use-full-cv";
import { CV_SECTIONS, countEntries, SECTION_CONFIG } from "../lib/sections";
import type { CvSection } from "../types";
import { PublishCard } from "./publish-card";

/**
 * @component CvOverview
 * @description Overview de /cv: una card por seccion con el CONTEO de
 *   entradas (link a la sub-ruta) + la card de publicacion. Los 10 conteos
 *   se derivan de UN solo content.get-all (useFullCv) en vez de un fetch
 *   por seccion; si la query falla la card muestra un guion.
 */
interface SectionCardProps {
	section: CvSection;
	isLoading: boolean;
	count: number | null;
}

function SectionCard({ section, isLoading, count }: SectionCardProps) {
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
					{isLoading ? (
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
	const query = useFullCv();

	return (
		<section className="space-y-6">
			<h1 className="text-2xl font-semibold">Gestion de CV</h1>
			<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{CV_SECTIONS.map((section) => (
					<SectionCard
						key={section}
						section={section}
						isLoading={query.isLoading}
						count={
							query.data ? countEntries(section, query.data[section]) : null
						}
					/>
				))}
			</div>
			<PublishCard />
		</section>
	);
}
