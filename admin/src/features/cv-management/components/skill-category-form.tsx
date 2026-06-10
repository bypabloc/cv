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
import { skillCategoryToForm, skillCategoryToPayload } from "../lib/payloads";
import type { CvCatalogs, CvSkillCategory } from "../types";
import {
	SKILL_KIND_VALUES,
	type SkillCategoryFormValues,
	skillCategoryFormSchema,
} from "../validation";
import { BiLangField } from "./bilang-field";
import { NichePriorityPicker } from "./niche-priority-picker";
import { TagInput } from "./tag-input";

/**
 * @component SkillCategoryForm
 * @description Form de una categoria de skills: nombre BiLang, kind
 *   (technical/soft) y skills ORDENADAS (tag-input con reorden interno; el
 *   orden es el de presentacion en el sitio) + niches/prioridad. Emite el
 *   payload del contrato upsert-skill-category.
 *
 * @props {CvSkillCategory} [initial] - Categoria a editar (ausente = alta)
 * @props {(payload: CvSkillCategory) => void} onSubmit - Payload validado
 * @props {boolean} submitting - Mutation en vuelo
 * @props {CvCatalogs} catalogs - Vocabularios (skills + niches)
 */
interface SkillCategoryFormProps {
	initial?: CvSkillCategory;
	onSubmit: (payload: CvSkillCategory) => void;
	submitting: boolean;
	catalogs: CvCatalogs;
}

export function SkillCategoryForm({
	initial,
	onSubmit,
	submitting,
	catalogs,
}: SkillCategoryFormProps) {
	const form = useForm<SkillCategoryFormValues>({
		resolver: zodResolver(skillCategoryFormSchema),
		defaultValues: skillCategoryToForm(initial),
	});

	const handleSubmit = form.handleSubmit((values) => {
		onSubmit(skillCategoryToPayload(values));
	});

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
									placeholder="mi-categoria"
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
						<BiLangField
							name="name"
							label="Nombre"
							value={field.value}
							onChange={field.onChange}
							errors={{
								es: form.formState.errors.name?.es?.message,
								en: form.formState.errors.name?.en?.message,
							}}
						/>
					)}
				/>

				<FormField
					control={form.control}
					name="kind"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Tipo</FormLabel>
							<Select value={field.value} onValueChange={field.onChange}>
								<FormControl>
									<SelectTrigger data-testid="cv-field-kind">
										<SelectValue placeholder="Selecciona" />
									</SelectTrigger>
								</FormControl>
								<SelectContent>
									{SKILL_KIND_VALUES.map((value) => (
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
					name="skills"
					render={({ field }) => (
						<TagInput
							name="skills"
							label="Skills (ordenadas)"
							value={field.value}
							onChange={field.onChange}
							suggestions={catalogs.skills.map((skill) => skill.name)}
							reorderable
							error={form.formState.errors.skills?.message}
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
