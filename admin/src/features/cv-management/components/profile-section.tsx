"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { useCatalogs } from "../hooks/use-catalogs";
import { useCvSection } from "../hooks/use-cv-section";
import { useUpsertEntity } from "../hooks/use-upsert-entity";
import type { CvCatalogs, CvProfile } from "../types";
import { ProfileForm } from "./profile-form";

/**
 * @component ProfileSection
 * @description Pantalla del profile singleton: hidrata el form con el GET
 *   /cv?action=profile y guarda via upsert-profile. Skeleton mientras
 *   cargan profile + catalogos (el form necesita ambos para montar los
 *   defaults una sola vez).
 */
const EMPTY_CATALOGS: CvCatalogs = { niches: [], skills: [], techTags: [] };

export function ProfileSection() {
	const profileQuery = useCvSection<CvProfile>("profile");
	const catalogsQuery = useCatalogs();
	const upsert = useUpsertEntity("profile");

	if (profileQuery.isLoading || catalogsQuery.isLoading) {
		return (
			<div className="space-y-3" data-testid="cv-profile-skeleton">
				<Skeleton className="h-9 w-full" />
				<Skeleton className="h-9 w-full" />
				<Skeleton className="h-24 w-full" />
			</div>
		);
	}

	return (
		<section className="space-y-4">
			<h2 className="text-xl font-semibold">Perfil</h2>
			<ProfileForm
				initial={profileQuery.data}
				onSubmit={(payload) => upsert.mutate(payload)}
				submitting={upsert.isPending}
				catalogs={catalogsQuery.data ?? EMPTY_CATALOGS}
			/>
		</section>
	);
}
