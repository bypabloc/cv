"use client";

import type { ReactNode } from "react";
import { CvShell } from "@/features/cv-management";

/**
 * @layout CvLayout
 * @description Layout de /cv/**: gate admin-only + sub-nav de secciones
 *   (feature cv-management, componente CvShell).
 */
export default function CvLayout({ children }: { children: ReactNode }) {
	return <CvShell>{children}</CvShell>;
}
