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
import { profileToForm, profileToPayload } from "../lib/payloads";
import type { CvCatalogs, CvProfile } from "../types";
import { type ProfileFormValues, profileFormSchema } from "../validation";
import { BiLangField } from "./bilang-field";
import { NichePriorityPicker } from "./niche-priority-picker";

/**
 * @component ProfileForm
 * @description Form del profile singleton: nombre/handle, headline/summary
 *   BiLang, availability opcional, contactos, avatar, stats (4 contadores)
 *   y niches (sin prioridad: el profile no se reordena). Emite el payload
 *   del contrato upsert-profile.
 *
 * @props {CvProfile} [initial] - Profile actual (hidrata el form)
 * @props {(payload: CvProfile) => void} onSubmit - Payload validado
 * @props {boolean} submitting - Mutation en vuelo
 * @props {CvCatalogs} catalogs - Catalogo de niches
 */
interface ProfileFormProps {
	initial?: CvProfile;
	onSubmit: (payload: CvProfile) => void;
	submitting: boolean;
	catalogs: CvCatalogs;
}

const STATS_FIELDS = [
	{ name: "yearsExperience", label: "Anos de experiencia" },
	{ name: "companies", label: "Empresas" },
	{ name: "countries", label: "Paises" },
	{ name: "certifications", label: "Certificaciones" },
] as const;

const CONTACT_FIELDS = [
	{ name: "email", label: "Email" },
	{ name: "phone", label: "Telefono (opcional)" },
	{ name: "linkedin", label: "LinkedIn" },
	{ name: "github", label: "GitHub" },
	{ name: "website", label: "Website (opcional)" },
] as const;

export function ProfileForm({
	initial,
	onSubmit,
	submitting,
	catalogs,
}: ProfileFormProps) {
	const form = useForm<ProfileFormValues>({
		resolver: zodResolver(profileFormSchema),
		defaultValues: profileToForm(initial),
	});

	const handleSubmit = form.handleSubmit((values) => {
		onSubmit(profileToPayload(values));
	});

	return (
		<Form {...form}>
			<form onSubmit={handleSubmit} className="space-y-4" noValidate>
				<div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
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
					<FormField
						control={form.control}
						name="handle"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Handle</FormLabel>
								<FormControl>
									<Input data-testid="cv-field-handle" {...field} />
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
				</div>

				<FormField
					control={form.control}
					name="headline"
					render={({ field }) => (
						<BiLangField
							name="headline"
							label="Headline"
							value={field.value}
							onChange={field.onChange}
							errors={{
								es: form.formState.errors.headline?.es?.message,
								en: form.formState.errors.headline?.en?.message,
							}}
						/>
					)}
				/>

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
					name="availability"
					render={({ field }) => (
						<BiLangField
							name="availability"
							label="Disponibilidad (opcional)"
							value={field.value}
							onChange={field.onChange}
							errors={{
								es: form.formState.errors.availability?.es?.message,
								en: form.formState.errors.availability?.en?.message,
							}}
						/>
					)}
				/>

				<div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<FormField
						control={form.control}
						name="location"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Ubicacion</FormLabel>
								<FormControl>
									<Input data-testid="cv-field-location" {...field} />
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
					<FormField
						control={form.control}
						name="avatarUrl"
						render={({ field }) => (
							<FormItem>
								<FormLabel>Avatar URL</FormLabel>
								<FormControl>
									<Input data-testid="cv-field-avatarUrl" {...field} />
								</FormControl>
								<FormMessage />
							</FormItem>
						)}
					/>
				</div>

				<fieldset className="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<legend className="mb-2 text-sm font-medium">Contactos</legend>
					{CONTACT_FIELDS.map((contact) => (
						<FormField
							key={contact.name}
							control={form.control}
							name={contact.name}
							render={({ field }) => (
								<FormItem>
									<FormLabel>{contact.label}</FormLabel>
									<FormControl>
										<Input
											data-testid={`cv-field-${contact.name}`}
											{...field}
										/>
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>
					))}
				</fieldset>

				<fieldset className="grid grid-cols-2 gap-4 sm:grid-cols-4">
					<legend className="mb-2 text-sm font-medium">Stats</legend>
					{STATS_FIELDS.map((stat) => (
						<FormField
							key={stat.name}
							control={form.control}
							name={stat.name}
							render={({ field }) => (
								<FormItem>
									<FormLabel>{stat.label}</FormLabel>
									<FormControl>
										<Input
											type="number"
											data-testid={`cv-field-${stat.name}`}
											{...field}
										/>
									</FormControl>
									<FormMessage />
								</FormItem>
							)}
						/>
					))}
				</fieldset>

				<FormField
					control={form.control}
					name="niches"
					render={({ field }) => (
						<NichePriorityPicker
							niches={catalogs.niches}
							selected={field.value}
							priority={{}}
							showPriority={false}
							onChange={(next) => field.onChange(next.niches)}
							error={form.formState.errors.niches?.message}
						/>
					)}
				/>

				<Button
					type="submit"
					data-testid="cv-form-submit"
					disabled={submitting}
				>
					{submitting ? "Guardando..." : "Guardar perfil"}
				</Button>
			</form>
		</Form>
	);
}
