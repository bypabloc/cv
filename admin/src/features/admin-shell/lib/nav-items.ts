import {
  BarChart3,
  FileText,
  type LucideIcon,
  Monitor,
  Settings,
  Users,
} from 'lucide-react'
import { ROUTES } from '@/lib/routes'

/**
 * @module nav-items
 * @description Items del sidebar del app shell. El slot `metrics` apunta a la
 *   raiz del area de metricas (las pantallas las monta el plan b-analytics-api;
 *   aqui solo el link). `adminOnly` oculta el item a usuarios no-admin.
 */
export interface NavItem {
  href: string
  label: string
  icon: LucideIcon
  adminOnly?: boolean
}

export const NAV_ITEMS: readonly NavItem[] = [
  { href: ROUTES.admin.metrics, label: 'Metricas', icon: BarChart3 },
  { href: ROUTES.admin.settings, label: 'Configuracion', icon: Settings },
  { href: ROUTES.admin.sessions, label: 'Mis sesiones', icon: Monitor },
  { href: ROUTES.admin.users, label: 'Usuarios', icon: Users, adminOnly: true },
  { href: ROUTES.admin.cv, label: 'Gestion CV', icon: FileText },
]
