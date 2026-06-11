"use client";

import {
	Award,
	BadgeCheck,
	Briefcase,
	ChevronRight,
	FolderGit2,
	GraduationCap,
	Languages,
	type LucideIcon,
	MessageSquareQuote,
	Newspaper,
	UserRound,
	Wrench,
} from "lucide-react";
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
const SECTION_ICONS: Record<CvSection, LucideIcon> = {
	profile: UserRound,
	experiences: Briefcase,
	projects: FolderGit2,
	skills: Wrench,
	education: GraduationCap,
	certificates: BadgeCheck,
	awards: Award,
	languages: Languages,
	endorsements: MessageSquareQuote,
	publications: Newspaper,
};

interface SectionCardProps {
	section: CvSection;
	isLoading: boolean;
	count: number | null;
}

function SectionCard({ section, isLoading, count }: SectionCardProps) {
	const Icon = SECTION_ICONS[section];
	return (
		<Link
			href={ROUTES.admin.cvSection(section)}
			data-testid={`cv-section-card-${section}`}
		>
			<Card className="group h-full transition-colors hover:border-primary/40 hover:bg-accent/50">
				<CardHeader className="flex flex-row items-center justify-between space-y-0">
					<CardTitle className="flex items-center gap-2 text-base">
						<Icon aria-hidden className="size-4 text-muted-foreground" />
						{SECTION_CONFIG[section].label}
					</CardTitle>
					<ChevronRight
						aria-hidden
						className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5"
					/>
				</CardHeader>
				<CardContent>
					{isLoading ? (
						<Skeleton className="h-8 w-10" />
					) : (
						<>
							<p
								className="text-2xl font-semibold"
								data-testid={`cv-section-count-${section}`}
							>
								{count ?? "—"}
							</p>
							<p className="text-xs text-muted-foreground">
								{count === 1 ? "entrada" : "entradas"}
							</p>
						</>
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
