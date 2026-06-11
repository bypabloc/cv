import { apiFetch } from "@/lib/api-client";
import type { Envelope } from "@/types/api";
import type {
	CvAward,
	CvCatalogs,
	CvCertificate,
	CvEducation,
	CvEndorsement,
	CvEntitySectionKind,
	CvExperience,
	CvFullAdmin,
	CvLanguage,
	CvProfile,
	CvProject,
	CvPublication,
	CvSection,
	CvSkillCategory,
	CvUpsertPayload,
	DeletePayload,
	DeleteResponse,
	PublishDispatchResponse,
	PublishStatusResponse,
	ReorderPayload,
	ReorderResponse,
	UpsertResponse,
} from "../types";

/**
 * @module features/cv-management/api/cv-admin-client
 * @description Cliente tipado de las operations admin del Lambda `cv`
 *   (admin-only via whitelist SSM; el viejo Lambda `cv_admin` se fusiono en
 *   `cv`): POST /cv con body `{operation: 'content'|'publish', action, data}`
 *   via apiFetch (Bearer + mutex + contrato FLAT). Un metodo por action
 *   (22 content + 2 publish) + dispatch generico por seccion
 *   (`upsertEntity`/`deleteEntity`) para los hooks parametrizados.
 */

function content<T>(action: string, data: unknown): Promise<Envelope<T>> {
	return apiFetch<Envelope<T>>("/cv", {
		method: "POST",
		body: { operation: "content", action, data },
	});
}

function publishOp<T>(action: string): Promise<Envelope<T>> {
	return apiFetch<Envelope<T>>("/cv", {
		method: "POST",
		body: { operation: "publish", action, data: {} },
	});
}

/** Action de upsert por seccion del admin. */
const UPSERT_ACTION: Record<CvSection, string> = {
	profile: "upsert-profile",
	experiences: "upsert-experience",
	projects: "upsert-project",
	education: "upsert-education",
	certificates: "upsert-certificate",
	awards: "upsert-award",
	languages: "upsert-language",
	endorsements: "upsert-endorsement",
	publications: "upsert-publication",
	skills: "upsert-skill-category",
};

/** Action de delete por seccion con lista (profile no se borra). */
const DELETE_ACTION: Record<CvEntitySectionKind, string> = {
	experiences: "delete-experience",
	projects: "delete-project",
	education: "delete-education",
	certificates: "delete-certificate",
	awards: "delete-award",
	languages: "delete-language",
	endorsements: "delete-endorsement",
	publications: "delete-publication",
	skills: "delete-skill-category",
};

/** Dispatch generico de upsert por seccion (lo usan los hooks). */
export function upsertEntity(
	section: CvSection,
	data: CvUpsertPayload,
): Promise<Envelope<UpsertResponse>> {
	return content<UpsertResponse>(UPSERT_ACTION[section], data);
}

/** Dispatch generico de delete por seccion (lo usan los hooks). */
export function deleteEntity(
	section: CvEntitySectionKind,
	data: DeletePayload,
): Promise<Envelope<DeleteResponse>> {
	return content<DeleteResponse>(DELETE_ACTION[section], data);
}

export const cvAdminClient = {
	// --- operation content: upserts ---
	upsertProfile: (data: CvProfile) =>
		content<UpsertResponse>("upsert-profile", data),
	upsertExperience: (data: CvExperience) =>
		content<UpsertResponse>("upsert-experience", data),
	upsertProject: (data: CvProject) =>
		content<UpsertResponse>("upsert-project", data),
	upsertEducation: (data: CvEducation) =>
		content<UpsertResponse>("upsert-education", data),
	upsertCertificate: (data: CvCertificate) =>
		content<UpsertResponse>("upsert-certificate", data),
	upsertAward: (data: CvAward) => content<UpsertResponse>("upsert-award", data),
	upsertLanguage: (data: CvLanguage) =>
		content<UpsertResponse>("upsert-language", data),
	upsertEndorsement: (data: CvEndorsement) =>
		content<UpsertResponse>("upsert-endorsement", data),
	upsertPublication: (data: CvPublication) =>
		content<UpsertResponse>("upsert-publication", data),
	upsertSkillCategory: (data: CvSkillCategory) =>
		content<UpsertResponse>("upsert-skill-category", data),

	// --- operation content: deletes ---
	deleteExperience: (data: DeletePayload) =>
		content<DeleteResponse>("delete-experience", data),
	deleteProject: (data: DeletePayload) =>
		content<DeleteResponse>("delete-project", data),
	deleteEducation: (data: DeletePayload) =>
		content<DeleteResponse>("delete-education", data),
	deleteCertificate: (data: DeletePayload) =>
		content<DeleteResponse>("delete-certificate", data),
	deleteAward: (data: DeletePayload) =>
		content<DeleteResponse>("delete-award", data),
	deleteLanguage: (data: DeletePayload) =>
		content<DeleteResponse>("delete-language", data),
	deleteEndorsement: (data: DeletePayload) =>
		content<DeleteResponse>("delete-endorsement", data),
	deletePublication: (data: DeletePayload) =>
		content<DeleteResponse>("delete-publication", data),
	deleteSkillCategory: (data: DeletePayload) =>
		content<DeleteResponse>("delete-skill-category", data),

	// --- operation content: transversales ---
	reorder: (data: ReorderPayload) => content<ReorderResponse>("reorder", data),
	catalogs: () => content<CvCatalogs>("catalogs", {}),
	/** CV completo en shape de edicion (las 10 secciones, sin filtrar). */
	getAll: () => content<CvFullAdmin>("get-all", {}),

	// --- operation publish ---
	publishDispatch: () => publishOp<PublishDispatchResponse>("dispatch"),
	publishStatus: () => publishOp<PublishStatusResponse>("status"),
};
