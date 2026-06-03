import {
	BarChart3,
	FileText,
	type LucideIcon,
	Monitor,
	Settings,
	ShieldCheck,
	Users,
} from "lucide-react";
import { ROUTES } from "@/lib/routes";

/**
 * @module nav-items
 * @description Items del sidebar del app shell. `adminOnly` oculta el item a
 *   usuarios no-admin.
 *
 *   El area de metricas (Lambda analytics, plan b-analytics-api) entra por el
 *   item `Metricas` (ROUTES.admin.metrics). Las sub-secciones del tracking de
 *   visitantes cuelgan de /metrics/* (sessions, events, visits, geo, devices,
 *   funnel, contacts) y se navegan desde la page /metrics; el sidebar solo
 *   expone la raiz para no saturarlo.
 */
export interface NavItem {
	href: string;
	label: string;
	icon: LucideIcon;
	adminOnly?: boolean;
}

export const NAV_ITEMS: readonly NavItem[] = [
	{ href: ROUTES.admin.metrics, label: "Metricas", icon: BarChart3 },
	{ href: ROUTES.admin.settings, label: "Configuracion", icon: Settings },
	{
		href: ROUTES.admin.settingsSecurity,
		label: "Seguridad",
		icon: ShieldCheck,
	},
	{ href: ROUTES.admin.sessions, label: "Mis sesiones", icon: Monitor },
	{ href: ROUTES.admin.users, label: "Usuarios", icon: Users, adminOnly: true },
	{ href: ROUTES.admin.cv, label: "Gestion CV", icon: FileText },
];
