import {
	FileText,
	type LucideIcon,
	Monitor,
	Settings,
	Users,
} from "lucide-react";
import { ROUTES } from "@/lib/routes";

/**
 * @module nav-items
 * @description Items del sidebar del app shell. `adminOnly` oculta el item a
 *   usuarios no-admin.
 *
 *   El slot `metrics` (ROUTES.admin.metrics) NO se lista todavia: las pantallas
 *   de metricas las monta el plan b-analytics-api y la page /metrics aun no
 *   existe (un link rompe la navegacion con un 404 del SPA fallback). Cuando
 *   ese plan monte la page, re-agregar
 *   `{ href: ROUTES.admin.metrics, label: "Metricas", icon: BarChart3 }`.
 */
export interface NavItem {
	href: string;
	label: string;
	icon: LucideIcon;
	adminOnly?: boolean;
}

export const NAV_ITEMS: readonly NavItem[] = [
	{ href: ROUTES.admin.settings, label: "Configuracion", icon: Settings },
	{ href: ROUTES.admin.sessions, label: "Mis sesiones", icon: Monitor },
	{ href: ROUTES.admin.users, label: "Usuarios", icon: Users, adminOnly: true },
	{ href: ROUTES.admin.cv, label: "Gestion CV", icon: FileText },
];
