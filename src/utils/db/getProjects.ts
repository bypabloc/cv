import {
  db,
  eq,
  Projects,
  ProjectUrls,
  ProjectUrlTypes,
  inArray,
  Translations,
  Languages,
  sql,
} from "astro:db";

/**
 * Consulta que devuelve todos los proyectos de un usuario, incluyendo las traducciones y URLs.
 *
 * @param {object} user - Objeto del usuario para filtrar.
 * @param {string} [status] - Estado del proyecto para filtrar.
 * @param {string} [languageCode="en"] - Código del idioma para las traducciones.
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
    let languageId;

    try {
      // Obtener el ID del idioma correspondiente al código de idioma
      const languageQuery = db
        .select({ id: Languages.id })
        .from(Languages)
        .where(eq(Languages.codeName, languageCode));

      const languageResult = await languageQuery.execute();
      languageId = languageResult[0]?.id;

      if (!languageId) {
        return {
          isValid: false,
          message: `Language code ${languageCode} not found`,
        };
      }
    } catch (error) {
      console.error("Error al obtener el ID del idioma:", error);
      return {
        isValid: false,
        message: "Error al obtener el ID del idioma",
      };
    }

    let projects;

    try {
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
            ${Projects.description})`.as("description"),
          highlights: sql`COALESCE(
            (SELECT ${Translations.translatedValue}
             FROM ${Translations}
             WHERE ${Translations.recordId} = Projects.${Projects.id}
               AND ${Translations.tableName} = 'Projects'
               AND ${Translations.field} = 'highlights'
               AND ${Translations.languageId} = ${languageId}),
            ${Projects.highlights})`.as("highlights"),
          url: Projects.url,
          serviceStatus: Projects.serviceStatus,
        })
        .from(Projects)
        .where(eq(Projects.userId, user.id));

      if (status) {
        projectsQuery.where(eq(Projects.status, status));
      }

      projects = await projectsQuery.execute();

      if (!projects.length) {
        console.error("Proyectos no encontrados");
        return {
          isValid: false,
          message: "Proyectos no encontrados",
        };
      }
    } catch (error) {
      console.error("Error al obtener los proyectos:", error);
      return {
        isValid: false,
        message: "Error al obtener los proyectos",
      };
    }

    let projectUrls;

    try {
      // Obtener las URLs de los proyectos
      const projectIds = projects.map((project) => project.id);

      const projectUrlsQuery = db
        .select({
          projectId: ProjectUrls.projectId,
          urlType: ProjectUrlTypes.codeName,
          icons: ProjectUrlTypes.icons,
          url: ProjectUrls.url,
        })
        .from(ProjectUrls)
        .innerJoin(
          ProjectUrlTypes,
          eq(ProjectUrls.urlTypeId, ProjectUrlTypes.id)
        )
        .where(inArray(ProjectUrls.projectId, projectIds));

      const sqlRaw = projectUrlsQuery.toSQL();

      projectUrls = await projectUrlsQuery.execute();
    } catch (error) {
      console.error("Error al obtener las URLs de los proyectos:", error);
      return {
        isValid: false,
        message: "Error al obtener las URLs de los proyectos",
      };
    }

    // Agrupar las URLs por proyecto
    const urlsByProjectId = projectUrls.reduce((acc, url) => {
      if (!acc[url.projectId]) {
        acc[url.projectId] = [];
      }
      acc[url.projectId].push({
        type: url.urlType,
        url: url.url,
        icons: url.icons,
      });
      return acc;
    }, {});

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
        urls: urlsByProjectId[project.id] || [],
      };
    });

    // console.log(
    //   "Proyectos del usuario obtenidos correctamente:",
    //   JSON.stringify(formattedProjects, null, 2)
    // );

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
