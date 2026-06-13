"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { simpleEntityToForm, simpleEntityToPayload } from "../lib/payloads";
import {
	buildSimpleEntitySchema,
	SIMPLE_ENTITY_FIELDS,
	type SimpleEntityFormValues,
	type SimpleEntityKind,
	type SimpleFieldDef,
} from "../lib/simple-entities";
import type { CvCatalogs } from "../types";
import { BiLangField } from "./bilang-field";
import { NichePriorityPicker } from "./niche-priority-picker";

/**
 * @component SimpleEntityForm
 * @description Form parametrizado de las 6 entidades planas (education,
 *   certificate, award, language, endorsement, publication): renderiza los
 *   campos declarados en SIMPLE_ENTITY_FIELDS (text/date/bilang) + slug +
 *   niches/prioridad, valida con el Zod schema dinamico y emite el payload
 *   del upsert correspondiente.
 *
 * @props {SimpleEntityKind} entity - Entidad a editar
 * @props {Record<string, unknown>} [initial] - Record crudo a editar
 * @props {(payload: Record<string, unknown>) => void} onSubmit
 * @props {boolean} submitting - Mutation en vuelo
 * @props {CvCatalogs} catalogs - Catalogo de niches
 */
interface SimpleEntityFormProps {
	entity: SimpleEntityKind;
	initial?: Record<string, unknown>;
	onSubmit: (payload: Record<string, unknown>) => void;
	submitting: boolean;
	catalogs: CvCatalogs;
}

function fieldError(
	errors: Record<string, unknown>,
	name: string,
): { es?: string; en?: string; root?: string } {
	const error = errors[name] as
		| { message?: string; es?: { message?: string }; en?: { message?: string } }
		| undefined;
	return {
		root: error?.message,
		es: error?.es?.message,
		en: error?.en?.message,
	};
}

export function SimpleEntityForm({
	entity,
	initial,
	onSubmit,
	submitting,
	catalogs,
}: SimpleEntityFormProps) {
	const form = useForm<SimpleEntityFormValues>({
		resolver: zodResolver(buildSimpleEntitySchema(entity)),
		defaultValues: simpleEntityToForm(entity, initial),
	});

	const handleSubmit = form.handleSubmit((values) => {
		onSubmit(simpleEntityToPayload(entity, values));
	});

	const errors = form.formState.errors as Record<string, unknown>;

	const renderField = (field: SimpleFieldDef) => {
		if (field.kind === "bilang" || field.kind === "bilang-multiline") {
			return (
				<Controller
					key={field.name}
					control={form.control}
					name={field.name}
					render={({ field: controller }) => (
						<BiLangField
							name={field.name}
							label={field.label}
							multiline={field.kind === "bilang-multiline"}
							value={controller.value as { es: string; en: string }}
							onChange={controller.onChange}
							errors={fieldError(errors, field.name)}
						/>
					)}
				/>
			);
		}
		const error = fieldError(errors, field.name).root;
		return (
			<div key={field.name} className="space-y-1.5">
				<Label htmlFor={`cv-field-${field.name}`}>{field.label}</Label>
				<Input
					id={`cv-field-${field.name}`}
					data-testid={`cv-field-${field.name}`}
					placeholder={field.kind === "date" ? "YYYY-MM" : undefined}
					aria-invalid={error ? true : undefined}
					{...form.register(field.name)}
				/>
				{error ? (
					<p className="text-sm text-destructive" role="alert">
						{error}
					</p>
				) : null}
			</div>
		);
	};

	const slugError = fieldError(errors, "slug").root;

	return (
		<form onSubmit={handleSubmit} className="space-y-4" noValidate>
			<div className="space-y-1.5">
				<Label htmlFor="cv-field-slug">Slug</Label>
				<Input
					id="cv-field-slug"
					data-testid="cv-field-slug"
					placeholder="mi-entrada"
					disabled={initial !== undefined}
					aria-invalid={slugError ? true : undefined}
					{...form.register("slug")}
				/>
				{slugError ? (
					<p className="text-sm text-destructive" role="alert">
						{slugError}
					</p>
				) : null}
			</div>

			{SIMPLE_ENTITY_FIELDS[entity].map(renderField)}

			<Controller
				control={form.control}
				name="niches"
				render={({ field }) => (
					<NichePriorityPicker
						niches={catalogs.niches}
						selected={field.value as string[]}
						priority={form.watch("priority") as Record<string, number>}
						onChange={(next) => {
							field.onChange(next.niches);
							form.setValue("priority", next.priority);
						}}
						error={fieldError(errors, "niches").root}
					/>
				)}
			/>

			<Button type="submit" data-testid="cv-form-submit" disabled={submitting}>
				{submitting ? "Guardando..." : "Guardar"}
			</Button>
		</form>
	);
}
