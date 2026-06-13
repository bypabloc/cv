"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

/**
 * @component BiLangField
 * @description Par de inputs/textarea es | en lado a lado para un campo
 *   BiLang (label unico, dos columnas, responsive a 1 columna). Controlado:
 *   el form lo cablea via Controller y recibe siempre `{es, en}` strings.
 *
 * @props {string} name - Identificador del campo (data-testid bilang-<name>-es/en)
 * @props {string} label - Label unico del par
 * @props {{es: string, en: string}} value - Valor controlado
 * @props {(next: {es: string, en: string}) => void} onChange - Cambio de cualquier locale
 * @props {boolean} [multiline] - Textarea en vez de Input (default: false)
 * @props {{es?: string, en?: string}} [errors] - Mensajes de error por locale
 */
interface BiLangFieldProps {
	name: string;
	label: string;
	value: { es: string; en: string };
	onChange: (next: { es: string; en: string }) => void;
	multiline?: boolean;
	errors?: { es?: string; en?: string };
}

const LOCALES = ["es", "en"] as const;

export function BiLangField({
	name,
	label,
	value,
	onChange,
	multiline = false,
	errors,
}: BiLangFieldProps) {
	return (
		<div className="space-y-1.5" data-testid={`bilang-field-${name}`}>
			<Label>{label}</Label>
			<div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
				{LOCALES.map((locale) => {
					const error = errors?.[locale];
					const inputId = `bilang-${name}-${locale}`;
					const sharedProps = {
						id: inputId,
						"data-testid": inputId,
						value: value[locale],
						"aria-invalid": error ? true : undefined,
						onChange: (
							event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
						) => onChange({ ...value, [locale]: event.target.value }),
					};
					return (
						<div key={locale} className="space-y-1">
							<span
								className={cn(
									"font-mono text-[10px] uppercase tracking-widest",
									error ? "text-destructive" : "text-muted-foreground",
								)}
							>
								{locale}
							</span>
							{multiline ? (
								<Textarea {...sharedProps} />
							) : (
								<Input {...sharedProps} />
							)}
							{error ? (
								<p className="text-sm text-destructive" role="alert">
									{error}
								</p>
							) : null}
						</div>
					);
				})}
			</div>
		</div>
	);
}
