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
import { experienceToForm, experienceToPayload } from "../lib/payloads";
import type { CvCatalogs, CvExperience } from "../types";
import {
	type ExperienceFormValues,
	experienceFormSchema,
	SENIORITY_VALUES,
} from "../validation";
import { BiLangField } from "./bilang-field";
import { BiLangListEditor } from "./bilang-list-editor";
import { NichePriorityPicker } from "./niche-priority-picker";
import { TagInput } from "./tag-input";

/**
 * @component ExperienceForm
 * @description Form de alta/edicion de una experiencia: role BiLang,
 *   empresa/pais/fechas/seniority, bullets paralelos es/en
 *   (responsibilities/achievements), skills tecnicas/blandas con
 *   sugerencias del catalogo y niches+prioridad. Emite el payload del
 *   contrato upsert-experience (NO llama la mutation).
 *
 * @props {CvExperience} [initial] - Entidad a editar (ausente = alta)
 * @props {(payload: CvExperience) => void} onSubmit - Payload validado
 * @props {boolean} submitting - Mutation en vuelo
 * @props {CvCatalogs} catalogs - Vocabularios para selects/sugerencias
 */
interface ExperienceFormProps {
	initial?: CvExperience;
	onSubmit: (payload: CvExperience) => void;
	submitting: boolean;
	catalogs: CvCatalogs;
}

export function ExperienceForm({
	initial,
	onSubmit,
	submitting,
	catalogs,
}: ExperienceFormProps) {
	const form = useForm<ExperienceFormValues>({
		resolver: zodResolver(experienceFormSchema),
		defaultValues: experienceToForm(initial),
	});

	const handleSubmit = form.handleSubmit((values) => {
		onSubmit(experienceToPayload(values));
	});

	const skillSuggestions = catalogs.skills.map((skill) => skill.name);

	return (
		<Form {...form}>
			<form onSubmit={handleSubmit} className="space-y-4" noValidate>
				<FormField
					control={form.control}
					name="slug"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Slug</FormLabel>
							<FormControl>
								<Input
									data-testid="cv-field-slug"
									placeholder="mi-experiencia"
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
					name="role"
					render={({ field }) => (
						<BiLangField
							name="role"
							label="Rol"
							value={field.value}
							onChange={field.onChange}
							errors={{
								es: form.formState.errors.role?.es?.message,
								en: form.formState.errors.role?.en?.message,
							}}
						/>
					)}
				/>

				<div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<FormField
						control={form.control}
						name="company"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Empresa</FormLabel>
								<FormControl>
									<Input data-testid="cv-field-company" {...field} />
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
					<FormField
						control={form.control}
						name="country"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Pais</FormLabel>
								<FormControl>
									<Input data-testid="cv-field-country" {...field} />
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
				</div>

				<FormField
					control={form.control}
					name="companyUrl"
					render={({ field }) => (
						<FormItem>
							<FormLabel>URL de la empresa (opcional)</FormLabel>
							<FormControl>
								<Input data-testid="cv-field-companyUrl" {...field} />
							</FormControl>
							<FormMessage />
						</FormItem>
					)}
				/>

				<div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
					<FormField
						control={form.control}
						name="start"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Inicio</FormLabel>
								<FormControl>
									<Input
										data-testid="cv-field-start"
										placeholder="YYYY-MM"
										{...field}
									/>
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
					<FormField
						control={form.control}
						name="end"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Fin (vacio = presente)</FormLabel>
								<FormControl>
									<Input
										data-testid="cv-field-end"
										placeholder="YYYY-MM"
										{...field}
									/>
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
					<FormField
						control={form.control}
						name="seniority"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Seniority</FormLabel>
								<Select value={field.value} onValueChange={field.onChange}>
									<FormControl>
										<SelectTrigger data-testid="cv-field-seniority">
											<SelectValue placeholder="Selecciona" />
										</SelectTrigger>
									</FormControl>
									<SelectContent>
										{SENIORITY_VALUES.map((value) => (
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

				<FormField
					control={form.control}
					name="summary"
					render={({ field }) => (
						<BiLangField
							name="summary"
							label="Resumen (opcional)"
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

				<FormField
					control={form.control}
					name="responsibilities"
					render={({ field }) => (
						<BiLangListEditor
							name="responsibilities"
							label="Responsabilidades"
							value={field.value}
							onChange={field.onChange}
							error={form.formState.errors.responsibilities?.message}
						/>
					)}
				/>

				<FormField
					control={form.control}
					name="achievements"
					render={({ field }) => (
						<BiLangListEditor
							name="achievements"
							label="Logros"
							value={field.value}
							onChange={field.onChange}
							error={form.formState.errors.achievements?.message}
						/>
					)}
				/>

				<FormField
					control={form.control}
					name="skillsTechnical"
					render={({ field }) => (
						<TagInput
							name="skillsTechnical"
							label="Skills tecnicas"
							value={field.value}
							onChange={field.onChange}
							suggestions={skillSuggestions}
						/>
					)}
				/>

				<FormField
					control={form.control}
					name="skillsSoft"
					render={({ field }) => (
						<TagInput
							name="skillsSoft"
							label="Skills blandas"
							value={field.value}
							onChange={field.onChange}
							suggestions={skillSuggestions}
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
