"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import {
	Form,
	FormControl,
	FormField,
	FormItem,
	FormLabel,
	FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { projectToForm, projectToPayload } from "../lib/payloads";
import type { CvCatalogs, CvProject } from "../types";
import {
	PROJECT_STATUS_VALUES,
	PROJECT_TYPE_VALUES,
	type ProjectFormValues,
	projectFormSchema,
} from "../validation";
import { BiLangField } from "./bilang-field";
import { NichePriorityPicker } from "./niche-priority-picker";
import { PairListEditor } from "./pair-list-editor";
import { TagInput } from "./tag-input";

/**
 * @component ProjectForm
 * @description Form de alta/edicion de un proyecto: summary/description
 *   BiLang, links {label,url}, metricas key/value ORDENADAS (con reorden),
 *   stack con sugerencias de tech-tags, case study (resumen + detallado
 *   problem/process/result = 6 textareas) y niches+prioridad. Emite el
 *   payload del contrato upsert-project.
 *
 * @props {CvProject} [initial] - Entidad a editar (ausente = alta)
 * @props {(payload: CvProject) => void} onSubmit - Payload validado
 * @props {boolean} submitting - Mutation en vuelo
 * @props {CvCatalogs} catalogs - Vocabularios para selects/sugerencias
 */
interface ProjectFormProps {
	initial?: CvProject;
	onSubmit: (payload: CvProject) => void;
	submitting: boolean;
	catalogs: CvCatalogs;
}

export function ProjectForm({
	initial,
	onSubmit,
	submitting,
	catalogs,
}: ProjectFormProps) {
	const form = useForm<ProjectFormValues>({
		resolver: zodResolver(projectFormSchema),
		defaultValues: projectToForm(initial),
	});

	const handleSubmit = form.handleSubmit((values) => {
		onSubmit(projectToPayload(values));
	});

	const stackSuggestions = catalogs.techTags.map((tag) => tag.name);

	return (
		<Form {...form}>
			<form onSubmit={handleSubmit} className="space-y-4" noValidate>
				<div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<FormField
						control={form.control}
						name="slug"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Slug</FormLabel>
								<FormControl>
									<Input
										data-testid="cv-field-slug"
										placeholder="mi-proyecto"
										disabled={initial !== undefined}
										{...field}
									/>
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
					<FormField
						control={form.control}
						name="name"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Nombre</FormLabel>
								<FormControl>
									<Input data-testid="cv-field-name" {...field} />
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
				</div>

				<FormField
					control={form.control}
					name="summary"
					render={({ field }) => (
						<BiLangField
							name="summary"
							label="Resumen"
							multiline
							value={field.value}
							onChange={field.onChange}
							errors={{
								es: form.formState.errors.summary?.es?.message,
								en: form.formState.errors.summary?.en?.message,
							}}
						/>
					)}
				/>

				<FormField
					control={form.control}
					name="description"
					render={({ field }) => (
						<BiLangField
							name="description"
							label="Descripcion (opcional)"
							multiline
							value={field.value}
							onChange={field.onChange}
							errors={{
								es: form.formState.errors.description?.es?.message,
								en: form.formState.errors.description?.en?.message,
							}}
						/>
					)}
				/>

				<div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<FormField
						control={form.control}
						name="url"
						render={({ field }) => (
							<FormItem>
								<FormLabel>URL (opcional)</FormLabel>
								<FormControl>
									<Input data-testid="cv-field-url" {...field} />
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
					<FormField
						control={form.control}
						name="repo"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Repositorio (opcional)</FormLabel>
								<FormControl>
									<Input data-testid="cv-field-repo" {...field} />
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
				</div>

				<FormField
					control={form.control}
					name="links"
					render={({ field }) => (
						<PairListEditor
							label="Links"
							keyLabel="Etiqueta"
							valueLabel="URL"
							value={field.value}
							onChange={field.onChange}
							testIdPrefix="cv-link"
							error={form.formState.errors.links?.message}
						/>
					)}
				/>

				<div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<FormField
						control={form.control}
						name="status"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Estado</FormLabel>
								<Select value={field.value} onValueChange={field.onChange}>
									<FormControl>
										<SelectTrigger data-testid="cv-field-status">
											<SelectValue placeholder="Selecciona" />
										</SelectTrigger>
									</FormControl>
									<SelectContent>
										{PROJECT_STATUS_VALUES.map((value) => (
											<SelectItem key={value} value={value}>
												{value}
											</SelectItem>
										))}
									</SelectContent>
								</Select>
								<FormMessage />
							</FormItem>
						)}
					/>
					<FormField
						control={form.control}
						name="projectType"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Tipo</FormLabel>
								<Select value={field.value} onValueChange={field.onChange}>
									<FormControl>
										<SelectTrigger data-testid="cv-field-projectType">
											<SelectValue placeholder="Selecciona" />
										</SelectTrigger>
									</FormControl>
									<SelectContent>
										{PROJECT_TYPE_VALUES.map((value) => (
											<SelectItem key={value} value={value}>
												{value}
											</SelectItem>
										))}
									</SelectContent>
								</Select>
								<FormMessage />
							</FormItem>
						)}
					/>
				</div>

				<div className="flex flex-wrap gap-6">
					<FormField
						control={form.control}
						name="isConfidential"
						render={({ field }) => (
							<FormItem className="flex items-center gap-2">
								<FormControl>
									<Switch
										data-testid="cv-field-isConfidential"
										checked={field.value}
										onCheckedChange={field.onChange}
									/>
								</FormControl>
								<FormLabel className="!mt-0">Confidencial</FormLabel>
							</FormItem>
						)}
					/>
					<FormField
						control={form.control}
						name="metricsEstimated"
						render={({ field }) => (
							<FormItem className="flex items-center gap-2">
								<FormControl>
									<Switch
										data-testid="cv-field-metricsEstimated"
										checked={field.value}
										onCheckedChange={field.onChange}
									/>
								</FormControl>
								<FormLabel className="!mt-0">Metricas estimadas</FormLabel>
							</FormItem>
						)}
					/>
				</div>

				<FormField
					control={form.control}
					name="stack"
					render={({ field }) => (
						<TagInput
							name="stack"
							label="Stack"
							value={field.value}
							onChange={field.onChange}
							suggestions={stackSuggestions}
						/>
					)}
				/>

				<FormField
					control={form.control}
					name="caseStudy"
					render={({ field }) => (
						<BiLangField
							name="caseStudy"
							label="Case study (resumen, opcional)"
							multiline
							value={field.value}
							onChange={field.onChange}
							errors={{
								es: form.formState.errors.caseStudy?.es?.message,
								en: form.formState.errors.caseStudy?.en?.message,
							}}
						/>
					)}
				/>

				<FormField
					control={form.control}
					name="caseStudyProblem"
					render={({ field }) => (
						<BiLangField
							name="caseStudyProblem"
							label="Case study: problema (opcional)"
							multiline
							value={field.value}
							onChange={field.onChange}
							errors={{
								es: form.formState.errors.caseStudyProblem?.es?.message,
								en: form.formState.errors.caseStudyProblem?.en?.message,
							}}
						/>
					)}
				/>

				<FormField
					control={form.control}
					name="caseStudyProcess"
					render={({ field }) => (
						<BiLangField
							name="caseStudyProcess"
							label="Case study: proceso (opcional)"
							multiline
							value={field.value}
							onChange={field.onChange}
							errors={{
								es: form.formState.errors.caseStudyProcess?.es?.message,
								en: form.formState.errors.caseStudyProcess?.en?.message,
							}}
						/>
					)}
				/>

				<FormField
					control={form.control}
					name="caseStudyResult"
					render={({ field }) => (
						<BiLangField
							name="caseStudyResult"
							label="Case study: resultado (opcional)"
							multiline
							value={field.value}
							onChange={field.onChange}
							errors={{
								es: form.formState.errors.caseStudyResult?.es?.message,
								en: form.formState.errors.caseStudyResult?.en?.message,
							}}
						/>
					)}
				/>

				<FormField
					control={form.control}
					name="metrics"
					render={({ field }) => (
						<PairListEditor
							label="Metricas (ordenadas)"
							keyLabel="Clave"
							valueLabel="Valor"
							value={field.value}
							onChange={field.onChange}
							testIdPrefix="cv-metric"
							reorderable
							error={form.formState.errors.metrics?.message}
						/>
					)}
				/>

				<FormField
					control={form.control}
					name="niches"
					render={({ field }) => (
						<NichePriorityPicker
							niches={catalogs.niches}
							selected={field.value}
							priority={form.watch("priority")}
							onChange={(next) => {
								field.onChange(next.niches);
								form.setValue("priority", next.priority);
							}}
							error={form.formState.errors.niches?.message}
						/>
					)}
				/>

				<Button
					type="submit"
					data-testid="cv-form-submit"
					disabled={submitting}
				>
					{submitting ? "Guardando..." : "Guardar"}
				</Button>
			</form>
		</Form>
	);
}
