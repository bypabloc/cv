import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * @component LoadingSpinner
 * @description Spinner accesible (role=status + aria-label).
 * @props {string} [className] - clases extra
 * @props {string} [label] - aria-label (default 'Cargando')
 */
export function LoadingSpinner({
	className,
	label = "Cargando",
}: {
	className?: string;
	label?: string;
}) {
	return (
		<span role="status" aria-label={label}>
			<Loader2 className={cn("h-4 w-4 animate-spin", className)} />
		</span>
	);
}
