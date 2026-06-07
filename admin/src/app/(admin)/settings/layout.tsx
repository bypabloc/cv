"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";

/**
 * @page SettingsLayout
 * @description Layout de /settings con tabs como RUTAS reales: Perfil y cuenta
 *   (/settings), Seguridad (/settings/security) y Sesiones (/settings/sessions).
 *   El tab activo se deriva de usePathname; cada page renderiza su contenido.
 */
const TABS = [
	{ href: ROUTES.admin.settings, label: "Perfil y cuenta" },
	{ href: ROUTES.admin.settingsSecurity, label: "Seguridad" },
	{ href: ROUTES.admin.settingsSessions, label: "Sesiones" },
] as const;

export default function SettingsLayout({ children }: { children: ReactNode }) {
	const pathname = usePathname();

	return (
		<section className="mx-auto max-w-4xl space-y-6">
			<h1 className="text-2xl font-semibold">Configuracion</h1>

			<nav
				aria-label="Secciones de configuracion"
				className="inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground"
			>
				{TABS.map((tab) => {
					const active =
						tab.href === ROUTES.admin.settings
							? pathname === tab.href
							: pathname.startsWith(tab.href);
					return (
						<Link
							key={tab.href}
							href={tab.href}
							aria-current={active ? "page" : undefined}
							className={cn(
								"inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
								active
									? "bg-background text-foreground shadow-sm"
									: "hover:text-foreground",
							)}
						>
							{tab.label}
						</Link>
					);
				})}
			</nav>

			{children}
		</section>
	);
}
