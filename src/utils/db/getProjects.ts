import { db, eq, Projects, Translations, Languages, sql } from "astro:db";

/**
 * Consulta que devuelve todos los proyectos de un usuario, incluyendo las traducciones.
 *
 * @param {object} user - Objeto del usuario para filtrar.
 * @param {string} [status] - Estado del proyecto para filtrar.
 * @param {string} [languageCode="es"] - Código del idioma para las traducciones.
 * @returns {Promise<ResponseFunction>} - Resultado de la consulta de los proyectos.
 */
export const getProjects = async ({
  status,
  user,
  languageCode = "en",
}: {
  status?: string;
  user: { id: string };
  languageCode?: string;
}): Promise<ResponseFunction> => {
  try {
    // Obtener el ID del idioma correspondiente al código de idioma
    const languageQuery = db
      .select({ id: Languages.id })
      .from(Languages)
      .where(eq(Languages.codeName, languageCode));

    const languageResult = await languageQuery.execute();
    const languageId = languageResult[0]?.id;

    if (!languageId) {
      return {
        isValid: false,
        message: `Language code ${languageCode} not found`,
      };
    }

    // Realizar la consulta principal incluyendo las traducciones
    const projectsQuery = db
      .select({
        id: Projects.id,
        status: Projects.status,
        name: Projects.name,
        description: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = Projects.${Projects.id}
             AND ${Translations.tableName} = 'Projects'
             AND ${Translations.field} = 'description'
             AND ${Translations.languageId} = ${languageId}),
          ${Projects.description}) AS description`,
        highlights: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = Projects.${Projects.id}
             AND ${Translations.tableName} = 'Projects'
             AND ${Translations.field} = 'highlights'
             AND ${Translations.languageId} = ${languageId}),
          ${Projects.highlights}) AS highlights`,
        url: Projects.url,
        serviceStatus: Projects.serviceStatus,
      })
      .from(Projects)
      .where(eq(Projects.userId, user.id));

    if (status) {
      projectsQuery.where(eq(Projects.status, status));
    }

    const projects = await projectsQuery.execute();

    if (!projects.length) {
      console.error("Proyectos no encontrados");
      return {
        isValid: false,
        message: "Proyectos no encontrados",
      };
    }

    // console.log("Proyectos encontrados:", JSON.stringify(projects, null, 2));

    // Convertir el campo `highlights` de cada resultado a un array de objetos si es necesario
    const formattedProjects = projects.map((project) => {
      let highlights = project.highlights;
      try {
        highlights = JSON.parse(project.highlights);
      } catch (e) {
        console.warn(
          `Error parsing JSON for highlights in project ${project.id}:`,
          e
        );
      }
      return {
        ...project,
        highlights,
      };
    });

    return {
      isValid: true,
      data: {
        projects: formattedProjects,
      },
    };
  } catch (error) {
    console.error("Error al obtener los proyectos del usuario:", error);
    return {
      isValid: false,
      message: "Error al obtener los proyectos del usuario",
    };
  }
};
