"use client";

import { useState } from "react";
import { useCatalogs } from "../hooks/use-catalogs";
import { useCvSection } from "../hooks/use-cv-section";
import { useDeleteEntity } from "../hooks/use-delete-entity";
import { useReorder } from "../hooks/use-reorder";
import { useUpsertEntity } from "../hooks/use-upsert-entity";
import { SECTION_CONFIG, toListItem } from "../lib/sections";
import { SECTION_SIMPLE_ENTITY } from "../lib/simple-entities";
import type {
	CvCatalogs,
	CvEntityRecord,
	CvEntitySectionKind,
	CvExperience,
	CvProject,
	CvSkillCategory,
	CvUpsertPayload,
} from "../types";
import { DeleteEntityDialog } from "./delete-entity-dialog";
import { EntityFormDialog } from "./entity-form-dialog";
import { ExperienceForm } from "./experience-form";
import { ProjectForm } from "./project-form";
import { SectionList } from "./section-list";
import { SimpleEntityForm } from "./simple-entity-form";
import { SkillCategoryForm } from "./skill-category-form";

/**
 * @component CvEntitySection
 * @description Pantalla completa de una seccion con lista del CV: lista de
 *   cards (orden por niche activo), alta/edicion en dialog con el form de
 *   la seccion, borrado con confirmacion y reorden (mutation reorder con la
 *   lista completa de slugs del niche). Cablea los hooks de la feature.
 *
 * @props {CvEntitySectionKind} section - Seccion de lista (no profile)
 */
interface CvEntitySectionProps {
	section: CvEntitySectionKind;
}

interface FormSlotProps {
	section: CvEntitySectionKind;
	initial: CvEntityRecord | undefined;
	onSubmit: (payload: CvUpsertPayload) => void;
	submitting: boolean;
	catalogs: CvCatalogs;
}

function FormSlot({
	section,
	initial,
	onSubmit,
	submitting,
	catalogs,
}: FormSlotProps) {
	if (section === "experiences") {
		return (
			<ExperienceForm
				// reason: la lista del GET /cv llega tipada por seccion (types.ts);
				// este switch fija la correspondencia seccion -> shape.
				initial={initial as CvExperience | undefined}
				onSubmit={onSubmit}
				submitting={submitting}
				catalogs={catalogs}
			/>
		);
	}
	if (section === "projects") {
		return (
			<ProjectForm
				// reason: idem — correspondencia seccion -> shape del record.
				initial={initial as CvProject | undefined}
				onSubmit={onSubmit}
				submitting={submitting}
				catalogs={catalogs}
			/>
		);
	}
	if (section === "skills") {
		return (
			<SkillCategoryForm
				// reason: idem — correspondencia seccion -> shape del record.
				initial={initial as CvSkillCategory | undefined}
				onSubmit={onSubmit}
				submitting={submitting}
				catalogs={catalogs}
			/>
		);
	}
	const entity = SECTION_SIMPLE_ENTITY[section];
	if (!entity) return null;
	return (
		<SimpleEntityForm
			entity={entity}
			// reason: las entidades simples se editan como record generico; el
			// payload que emite simpleEntityToPayload cumple el shape del upsert.
			initial={initial as Record<string, unknown> | undefined}
			onSubmit={(payload) => onSubmit(payload as unknown as CvUpsertPayload)}
			submitting={submitting}
			catalogs={catalogs}
		/>
	);
}

const EMPTY_CATALOGS: CvCatalogs = { niches: [], skills: [], techTags: [] };

export function CvEntitySection({ section }: CvEntitySectionProps) {
	const [activeNiche, setActiveNiche] = useState("");
	const [formOpen, setFormOpen] = useState(false);
	const [editingSlug, setEditingSlug] = useState<string | null>(null);
	const [deletingSlug, setDeletingSlug] = useState<string | null>(null);

	const niche = activeNiche === "" ? undefined : activeNiche;
	const listQuery = useCvSection<CvEntityRecord[]>(section, niche);
	const catalogsQuery = useCatalogs();
	const upsert = useUpsertEntity(section);
	const remove = useDeleteEntity(section);
	const reorder = useReorder(section);

	const records = listQuery.data ?? [];
	const items = records.map((record) => toListItem(section, record));
	const editing = editingSlug
		? records.find((record) => record.slug === editingSlug)
		: undefined;
	const catalogs = catalogsQuery.data ?? EMPTY_CATALOGS;
	const config = SECTION_CONFIG[section];

	const closeForm = (): void => {
		setFormOpen(false);
		setEditingSlug(null);
	};

	const handleSubmit = (payload: CvUpsertPayload): void => {
		upsert.mutate(payload, { onSuccess: closeForm });
	};

	const handleReorder = (orderedSlugs: string[]): void => {
		if (!niche || config.entityType === null) return;
		reorder.mutate({
			entity_type: config.entityType,
			niche,
			ordered_slugs: orderedSlugs,
		});
	};

	const handleDeleteConfirm = (): void => {
		if (!deletingSlug) return;
		remove.mutate(
			{ slug: deletingSlug },
			{ onSuccess: () => setDeletingSlug(null) },
		);
	};

	return (
		<section className="space-y-4">
			<h2 className="text-xl font-semibold">{config.label}</h2>

			<SectionList
				items={items}
				isLoading={listQuery.isLoading}
				niches={catalogs.niches}
				activeNiche={activeNiche}
				onNicheChange={setActiveNiche}
				onNew={() => {
					setEditingSlug(null);
					setFormOpen(true);
				}}
				onEdit={(slug) => {
					setEditingSlug(slug);
					setFormOpen(true);
				}}
				onDelete={setDeletingSlug}
				onReorder={handleReorder}
			/>

			<EntityFormDialog
				open={formOpen}
				// Sin trigger interno: el Dialog solo emite onOpenChange(false).
				onOpenChange={() => closeForm()}
				title={editing ? `Editar: ${editingSlug}` : "Nueva entrada"}
				description={config.label}
			>
				<FormSlot
					key={editingSlug ?? "new"}
					section={section}
					initial={editing}
					onSubmit={handleSubmit}
					submitting={upsert.isPending}
					catalogs={catalogs}
				/>
			</EntityFormDialog>

			<DeleteEntityDialog
				slug={deletingSlug}
				pending={remove.isPending}
				onConfirm={handleDeleteConfirm}
				onCancel={() => setDeletingSlug(null)}
			/>
		</section>
	);
}
