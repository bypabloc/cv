# Scope acordado — journey-3d-cv

Solo PLAN detallado, no implementacion (por ahora). Research COMPLETO
(3 informes en docs/progress/explore_*.md). Plan redactado en el README +
5 archivos de esta carpeta.

## Decisiones del usuario

- App NUEVA (apps/journey), basada en `generic` (recorrido completo, no un niche).
- Investigar AMBAS mecanicas (scroll-driven + POV navegable) + proponer mas ideas.
- Crear el plan de 2 proyectos/propuestas + variantes adicionales.
- Desktop-first 3D; en movil -> storytelling narrativo legible (fallback 2D/degradado).
- Angulo Fable 5 / Claude Code: como acelerar el build (no es engine 3D).
- Si alguna propuesta gusta mucho -> puede volverse el CV principal.

## Correccion del usuario (2026-07-02) — CRITICO, NO reabrir

- **El foco NO es el arco migratorio.** El eje protagonista es la
  **progresion profesional / seniority** (intern -> junior -> mid -> senior
  -> lead/arquitecto). La geografia es un GUINO SUTIL (etiqueta/bandera del
  cliente por estacion), NUNCA la columna vertebral.
- **Geografia real**: Pablo reside en **Lima, Peru**. Migro UNA sola vez
  (Venezuela -> Peru). Desde Peru trabaja REMOTO para clientes de Chile y
  Mexico. El campo `country` de cada experiencia es el pais del
  EMPLEADOR/CLIENTE, NO el lugar de residencia. NO existe un arco VE->PE->CL
  de residencia.
- El usuario abrio la puerta a **otros journeys en otras apps** con enfoques
  distintos (evolucion tecnica, impacto/proyectos) como propuestas paralelas.

## Datos reales disponibles (data-cache JSON, generado de la DB)

- 9 experiencias 2013-2026. Seniority: intern (2013) -> junior -> mid ->
  senior (2018) -> lead/arquitecto (2022-hoy). El `country` es el pais del
  cliente/empleador (VE hasta 2018; luego PE/CL como clientes), NO residencia.
- Residencia: Lima, Peru. Trabajo remoto para Chile y Mexico.
- stats: 12 anos, 8 empresas, 4 paises (de CLIENTES), 11 certs.
- skills: 7 categorias tecnicas (AI Workflows, Arquitectura, Backend,
  Cloud/DevOps, Datos/SQL, Dominios, Frontend) + 3 soft (liderazgo, mindset,
  equipo/cliente).
- profile, projects(4: ERP, fintech, microservicios...), education, awards,
  certificates, languages.

## Stack del proyecto

- Astro 6.3 estatico, React 18.3, Tailwind v4, Cloudflare Pages.
- generic ya arma el CV via CvSections + prebuild fetch-cache.
