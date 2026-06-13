/** @module features/cv-management — barrel explicito de la feature. */
export {
	cvAdminClient,
	deleteEntity,
	upsertEntity,
} from "./api/cv-admin-client";
export {
	CvReadError,
	cvReadClient,
	fetchCvSection,
} from "./api/cv-read-client";
export { cvKeys } from "./api/query-keys";
export { BiLangField } from "./components/bilang-field";
export { BiLangListEditor } from "./components/bilang-list-editor";
export { CvEntitySection } from "./components/cv-entity-section";
export { CvOverview } from "./components/cv-overview";
export { CvShell } from "./components/cv-shell";
export { DeleteEntityDialog } from "./components/delete-entity-dialog";
export { EntityFormDialog } from "./components/entity-form-dialog";
export { ExperienceForm } from "./components/experience-form";
export { NichePriorityPicker } from "./components/niche-priority-picker";
export { PairListEditor } from "./components/pair-list-editor";
export { ProfileForm } from "./components/profile-form";
export { ProfileSection } from "./components/profile-section";
export { ProjectForm } from "./components/project-form";
export { PublishCard } from "./components/publish-card";
export { SectionList } from "./components/section-list";
export { SimpleEntityForm } from "./components/simple-entity-form";
export { SkillCategoryForm } from "./components/skill-category-form";
export { useCatalogs } from "./hooks/use-catalogs";
export { useCvSection } from "./hooks/use-cv-section";
export { useDeleteEntity } from "./hooks/use-delete-entity";
export { useFullCv } from "./hooks/use-full-cv";
export { usePublish, usePublishStatus } from "./hooks/use-publish";
export { useReorder } from "./hooks/use-reorder";
export { useUpsertEntity } from "./hooks/use-upsert-entity";
export {
	CV_SECTIONS,
	countEntries,
	SECTION_CONFIG,
	toListItem,
} from "./lib/sections";
export type * from "./types";
