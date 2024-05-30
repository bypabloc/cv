import {
  db,
  eq,
  sql,
  Works,
  Skills,
  WorksTechnicalSkills,
  WorksSoftSkills,
  Keywords,
  SkillsKeywords,
  Employers,
  Translations,
  Languages,
} from "astro:db";

/**
 * Consulta que devuelve todas las experiencias laborales (Works)
 * incluyendo habilidades técnicas y blandas asociadas, organizadas en un objeto donde la clave es el ID de Works.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @param {string} [languageCode="es"] - Código del idioma para las traducciones.
 * @returns {Promise<object>} - Resultado de la consulta con experiencias laborales y habilidades asociadas.
 */
export const getWorks = async ({
  status,
  user,
  languageCode = "es",
}: {
  status?: string;
  user: { id: string };
  languageCode?: string;
} = {}): Promise<ResponseFunction> => {
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
        error: `Language code ${languageCode} not found`,
      };
    }

    // Realizar la consulta principal incluyendo las traducciones
    let query = db
      .select({
        id: Works.id,
        codeName: Works.codeName,
        name: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${Works.id}
             AND ${Translations.tableName} = 'Works'
             AND ${Translations.field} = 'name'
             AND ${Translations.languageId} = ${languageId}),
          ${Works.name}) AS name`,
        position: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${Works.id}
             AND ${Translations.tableName} = 'Works'
             AND ${Translations.field} = 'position'
             AND ${Translations.languageId} = ${languageId}),
          ${Works.position}) AS position`,
        startDate: Works.startDate,
        endDate: Works.endDate,
        responsibilitiesNProjects: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${Works.id}
             AND ${Translations.tableName} = 'Works'
             AND ${Translations.field} = 'responsibilitiesNProjects'
             AND ${Translations.languageId} = ${languageId}),
          ${Works.responsibilitiesNProjects}) AS responsibilitiesNProjects`,
        achievements: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${Works.id}
             AND ${Translations.tableName} = 'Works'
             AND ${Translations.field} = 'achievements'
             AND ${Translations.languageId} = ${languageId}),
          ${Works.achievements}) AS achievements`,
        summary: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${Works.id}
             AND ${Translations.tableName} = 'Works'
             AND ${Translations.field} = 'summary'
             AND ${Translations.languageId} = ${languageId}),
          ${Works.summary}) AS summary`,
        employer: Employers,
        technicalSkills: sql`(
          SELECT json_group_array(
            json_object(
              'id', Skills.id,
              'codeName', Skills.codeName,
              'name', COALESCE(
                (SELECT ${Translations.translatedValue}
                 FROM ${Translations}
                 WHERE ${Translations.recordId} = Skills.id
                   AND ${Translations.tableName} = 'Skills'
                   AND ${Translations.field} = 'name'
                   AND ${Translations.languageId} = ${languageId}),
                Skills.name),
              'description', COALESCE(
                (SELECT ${Translations.translatedValue}
                 FROM ${Translations}
                 WHERE ${Translations.recordId} = Skills.id
                   AND ${Translations.tableName} = 'Skills'
                   AND ${Translations.field} = 'description'
                   AND ${Translations.languageId} = ${languageId}),
                Skills.description),
              'type', Skills.type,
              'keywords', (SELECT json_group_array(json_object('id', Keywords.id, 'keys', Keywords.keys))
                          FROM SkillsKeywords
                          INNER JOIN Keywords ON Keywords.id = SkillsKeywords.keywordId
                          WHERE SkillsKeywords.skillId = Skills.id)
            )
          )
          FROM WorksTechnicalSkills
          INNER JOIN Skills ON Skills.id = WorksTechnicalSkills.technicalSkillId
          WHERE WorksTechnicalSkills.workId = Works.id
        )`,
        softSkills: sql`(
          SELECT json_group_array(
            json_object(
              'id', Skills.id,
              'codeName', Skills.codeName,
              'name', COALESCE(
                (SELECT ${Translations.translatedValue}
                 FROM ${Translations}
                 WHERE ${Translations.recordId} = Skills.id
                   AND ${Translations.tableName} = 'Skills'
                   AND ${Translations.field} = 'name'
                   AND ${Translations.languageId} = ${languageId}),
                Skills.name),
              'description', COALESCE(
                (SELECT ${Translations.translatedValue}
                 FROM ${Translations}
                 WHERE ${Translations.recordId} = Skills.id
                   AND ${Translations.tableName} = 'Skills'
                   AND ${Translations.field} = 'description'
                   AND ${Translations.languageId} = ${languageId}),
                Skills.description),
              'type', Skills.type,
              'keywords', (SELECT json_group_array(json_object('id', Keywords.id, 'keys', Keywords.keys))
                          FROM SkillsKeywords
                          INNER JOIN Keywords ON Keywords.id = SkillsKeywords.keywordId
                          WHERE SkillsKeywords.skillId = Skills.id)
            )
          )
          FROM WorksSoftSkills
          INNER JOIN Skills ON Skills.id = WorksSoftSkills.skillId
          WHERE WorksSoftSkills.workId = Works.id
        )`,
      })
      .from(Works)
      .leftJoin(Employers, eq(Employers.id, Works.employerId))
      .where(eq(Works.userId, user.id))
      .orderBy(
        sql`
          CASE
            WHEN ${Works.endDate} IS NULL THEN 0
            ELSE 1
          END,
          ${Works.endDate} DESC NULLS FIRST,
          ${Works.startDate} DESC
        `
      );

    if (status) {
      query = query.where(eq(Works.status, status));
    }

    const rawData = await query.execute();

    if (!rawData.length) {
      console.error("Experiencias laborales no encontradas");
      return {
        isValid: false,
        error: "Experiencias laborales no encontradas",
      };
    }

    // Convertir los campos JSON de string a arrays de objetos
    const formattedWorks = rawData.map((work) => {
      const safelyParseJSON = (field) => {
        try {
          return JSON.parse(field);
        } catch (e) {
          return field;
        }
      };

      const safelyParseKeywords = (skills) => {
        return skills.map((skill) => ({
          ...skill,
          keywords: Array.isArray(skill.keywords)
            ? skill.keywords.map((k) =>
                typeof k.keys === "string" ? safelyParseJSON(k.keys) : k.keys
              )
            : [],
        }));
      };

      return {
        ...work,
        responsibilitiesNProjects: safelyParseJSON(
          work.responsibilitiesNProjects
        ),
        achievements: safelyParseJSON(work.achievements),
        technicalSkills: safelyParseKeywords(
          safelyParseJSON(work.technicalSkills)
        ),
        softSkills: safelyParseKeywords(safelyParseJSON(work.softSkills)),
      };
    });

    // Agrupar por empleador, pero mantener los que no tienen empleador separados
    const groupedByEmployer = formattedWorks.reduce((acc, work) => {
      const employerId = work.employer?.id;
      if (employerId) {
        if (!acc[employerId]) {
          acc[employerId] = {
            employer: work.employer,
            works: [],
          };
        }
        acc[employerId].works.push(work);
      } else {
        acc[work.id] = {
          employer: null,
          works: [work],
        };
      }
      return acc;
    }, {});

    return {
      isValid: true,
      data: {
        works: groupedByEmployer,
      },
    };
  } catch (error) {
    console.error("Error al obtener las experiencias laborales:", error);
    return {
      isValid: false,
      error: "Error al obtener las experiencias laborales",
    };
  }
};
