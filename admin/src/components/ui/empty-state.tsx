import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * @component EmptyState
 * @description Estado vacio generico: icon + titulo + descripcion + accion.
 * @props {LucideIcon} [icon] - icono lucide
 * @props {string} title - titulo
 * @props {string} [description] - texto secundario
 * @props {ReactNode} [action] - boton/accion
 * @props {string} [className] - clases extra
 */
export function EmptyState({
	icon: Icon,
	title,
	description,
	action,
	className,
}: {
	icon?: LucideIcon;
	title: string;
	description?: string;
	action?: ReactNode;
	className?: string;
}) {
	return (
		<div
			className={cn(
				"flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed p-10 text-center",
				className,
			)}
		>
			{Icon ? <Icon className="h-10 w-10 text-muted-foreground" /> : null}
			<h3 className="font-medium">{title}</h3>
			{description ? (
				<p className="max-w-sm text-sm text-muted-foreground">{description}</p>
			) : null}
			{action}
		</div>
	);
}
