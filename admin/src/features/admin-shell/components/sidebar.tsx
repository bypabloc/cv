"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "../lib/nav-items";

/**
 * @component Sidebar
 * @description Navegacion lateral del app shell (desktop). Resalta el item
 *   activo segun el pathname. El item `Usuarios` (adminOnly) se muestra
 *   siempre; la page /users maneja el 404 del backend para no-admin
 *   (anti-enumeration).
 */
export function Sidebar() {
	const pathname = usePathname();
	return (
		<aside className="hidden h-screen w-60 shrink-0 border-r bg-card lg:flex lg:flex-col">
			<div className="p-6">
				<h2 className="font-mono text-sm uppercase tracking-widest text-muted-foreground">
					Admin
				</h2>
			</div>
			<nav className="flex-1 space-y-1 px-3">
				{NAV_ITEMS.map(({ href, label, icon: Icon }) => {
					const active = pathname === href || pathname.startsWith(`${href}/`);
					return (
						<Link
							key={href}
							href={href}
							className={cn(
								"flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
								active
									? "bg-accent text-accent-foreground"
									: "text-muted-foreground hover:bg-accent hover:text-foreground",
							)}
						>
							<Icon className="h-4 w-4" />
							{label}
						</Link>
					);
				})}
			</nav>
		</aside>
	);
}
