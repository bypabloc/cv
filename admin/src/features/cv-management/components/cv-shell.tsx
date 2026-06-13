"use client";

import { ShieldOff } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useIsAdmin } from "@/features/admin-shell/hooks/use-is-admin";
import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { CV_SECTIONS, SECTION_CONFIG } from "../lib/sections";

/**
 * @component CvShell
 * @description Marco de las pages /cv/**: gate admin-only (mismo
 *   tratamiento que users-admin: pantalla de no autorizado, NUNCA redirect
 *   a login ni crash) + sub-nav con las 10 secciones del CV. Mientras el
 *   rol no resuelve muestra skeleton.
 *
 * @props {ReactNode} children - La page de la seccion activa
 */
interface CvShellProps {
	children: ReactNode;
}

/**
 * @function normalizePathname
 * @description Quita el slash final del pathname (salvo la raiz "/"):
 *   `next.config.ts` usa `trailingSlash: true`, asi que en el export
 *   desplegado `usePathname()` devuelve '/cv/profile/' mientras los hrefs
 *   de ROUTES van sin slash — sin normalizar NINGUN tab matchea.
 */
function normalizePathname(pathname: string): string {
	return pathname.length > 1 && pathname.endsWith("/")
		? pathname.slice(0, -1)
		: pathname;
}

export function CvShell({ children }: CvShellProps) {
	const { isAdmin, isResolved } = useIsAdmin();
	const pathname = normalizePathname(usePathname());

	if (!isResolved) {
		return (
			<div className="space-y-3" data-testid="cv-shell-loading">
				<Skeleton className="h-8 w-full" />
				<Skeleton className="h-40 w-full" />
			</div>
		);
	}

	if (!isAdmin) {
		return (
			<EmptyState
				icon={ShieldOff}
				title="No tienes acceso a esta seccion"
				description="La gestion del CV esta disponible solo para administradores."
			/>
		);
	}

	return (
		<div className="space-y-6">
			<nav
				data-testid="cv-subnav"
				className="flex flex-wrap gap-1 border-b pb-2"
			>
				<Link
					href={ROUTES.admin.cv}
					data-testid="cv-subnav-overview"
					className={cn(
						"rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
						pathname === ROUTES.admin.cv
							? "bg-accent text-accent-foreground"
							: "text-muted-foreground hover:bg-accent hover:text-foreground",
					)}
				>
					Resumen
				</Link>
				{CV_SECTIONS.map((section) => {
					const href = ROUTES.admin.cvSection(section);
					return (
						<Link
							key={section}
							href={href}
							data-testid={`cv-subnav-${section}`}
							className={cn(
								"rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
								pathname === href
									? "bg-accent text-accent-foreground"
									: "text-muted-foreground hover:bg-accent hover:text-foreground",
							)}
						>
							{SECTION_CONFIG[section].label}
						</Link>
					);
				})}
			</nav>
			{children}
		</div>
	);
}
