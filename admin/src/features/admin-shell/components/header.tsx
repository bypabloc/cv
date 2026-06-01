"use client";

import {
	LogOut,
	Settings as SettingsIcon,
	User as UserIcon,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useLogout } from "@/features/auth/hooks/use-logout";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { ROUTES } from "@/lib/routes";
import { MobileSidebar } from "./mobile-sidebar";

/**
 * @component Header
 * @description Barra superior del app shell: spacer + ThemeToggle + menu de
 *   usuario (email + link a configuracion + logout).
 */
export function Header() {
	const user = useAuthStore((s) => s.user);
	const logout = useLogout();

	return (
		<header className="flex h-14 items-center gap-2 border-b bg-card px-4">
			<MobileSidebar />
			<div className="flex-1" />
			<ThemeToggle />
			<DropdownMenu>
				<DropdownMenuTrigger asChild>
					<Button variant="ghost" size="icon" aria-label="Menu de usuario">
						<UserIcon className="h-4 w-4" />
					</Button>
				</DropdownMenuTrigger>
				<DropdownMenuContent align="end" className="w-56">
					<DropdownMenuItem disabled className="opacity-100">
						<span className="truncate text-xs text-muted-foreground">
							{user?.email ?? "Sesion activa"}
						</span>
					</DropdownMenuItem>
					<DropdownMenuSeparator />
					<DropdownMenuItem asChild>
						<Link href={ROUTES.admin.settings}>
							<SettingsIcon className="mr-2 h-4 w-4" /> Configuracion
						</Link>
					</DropdownMenuItem>
					<DropdownMenuItem
						onClick={() => logout.mutate()}
						disabled={logout.isPending}
					>
						<LogOut className="mr-2 h-4 w-4" /> Cerrar sesion
					</DropdownMenuItem>
				</DropdownMenuContent>
			</DropdownMenu>
		</header>
	);
}
