import {
  db,
  eq,
  inArray,
  sql,
  Works,
  Skills,
  WorksTechnicalSkills,
  WorksSoftSkills,
  Keywords,
  SkillsKeywords,
  Users,
  Employers,
  Translations,
  Languages,
} from "astro:db";

/**
 * Consulta que devuelve todas las habilidades técnicas y blandas únicas,
 * incluyendo las traducciones correspondientes.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @param {string} [languageCode="es"] - Código del idioma para las traducciones.
 * @returns {Promise<object>} - Resultado de la consulta con habilidades técnicas y blandas únicas.
 */
export const getSkills = async ({
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

    // Consulta para obtener los IDs de las experiencias laborales del usuario
    let worksQuery = db
      .select({
        id: Works.id,
      })
      .from(Works)
      .where(eq(Works.userId, user.id));

    if (status) {
      worksQuery = worksQuery.where(eq(Works.status, status));
    }

    const worksData = await worksQuery.execute();
    const worksIds = worksData.map((item) => item.id);

    if (!worksIds.length) {
      console.error("Experiencias laborales no encontradas");
      return {
        isValid: false,
        error: "Experiencias laborales no encontradas",
      };
    }

    // Consulta para obtener las habilidades técnicas con traducciones
    const technicalSkillsQuery = db
      .select({
        id: Skills.id,
        codeName: Skills.codeName,
        name: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${Skills.id}
             AND ${Translations.tableName} = 'Skills'
             AND ${Translations.field} = 'name'
             AND ${Translations.languageId} = ${languageId}),
          ${Skills.name}) AS name`,
        description: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${Skills.id}
             AND ${Translations.tableName} = 'Skills'
             AND ${Translations.field} = 'description'
             AND ${Translations.languageId} = ${languageId}),
          ${Skills.description}) AS description`,
        type: Skills.type,
        keywords: sql`(
          SELECT json_group_array(json_object('id', Keywords.id, 'keys', Keywords.keys))
          FROM SkillsKeywords
          INNER JOIN Keywords ON Keywords.id = SkillsKeywords.keywordId
          WHERE SkillsKeywords.skillId = Skills.id
        ) AS keywords`,
      })
      .from(Skills)
      .innerJoin(
        WorksTechnicalSkills,
        eq(WorksTechnicalSkills.technicalSkillId, Skills.id)
      )
      .where(inArray(WorksTechnicalSkills.workId, worksIds));

    const technicalSkills = await technicalSkillsQuery.execute();

    // Consulta para obtener las habilidades blandas con traducciones
    const softSkillsQuery = db
      .select({
        id: Skills.id,
        codeName: Skills.codeName,
        name: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${Skills.id}
             AND ${Translations.tableName} = 'Skills'
             AND ${Translations.field} = 'name'
             AND ${Translations.languageId} = ${languageId}),
          ${Skills.name}) AS name`,
        description: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${Skills.id}
             AND ${Translations.tableName} = 'Skills'
             AND ${Translations.field} = 'description'
             AND ${Translations.languageId} = ${languageId}),
          ${Skills.description}) AS description`,
        type: Skills.type,
        keywords: sql`(
          SELECT json_group_array(json_object('id', Keywords.id, 'keys', Keywords.keys))
          FROM SkillsKeywords
          INNER JOIN Keywords ON Keywords.id = SkillsKeywords.keywordId
          WHERE SkillsKeywords.skillId = Skills.id
        ) AS keywords`,
      })
      .from(Skills)
      .innerJoin(WorksSoftSkills, eq(WorksSoftSkills.skillId, Skills.id))
      .where(inArray(WorksSoftSkills.workId, worksIds));

    const softSkills = await softSkillsQuery.execute();

    // Remover duplicados en habilidades técnicas
    const uniqueTechnicalSkills = [
      ...new Map(technicalSkills.map((skill) => [skill.id, skill])).values(),
    ];

    // Remover duplicados en habilidades blandas
    const uniqueSoftSkills = [
      ...new Map(softSkills.map((skill) => [skill.id, skill])).values(),
    ];

    // Función para analizar las cadenas JSON de palabras clave
    const safelyParseKeywords = (skills) => {
      return skills.map((skill) => ({
        ...skill,
        keywords: Array.isArray(skill.keywords)
          ? skill.keywords.map((k) =>
              typeof k.keys === "string" ? JSON.parse(k.keys) : k.keys
            )
          : [],
      }));
    };

    return {
      isValid: true,
      data: {
        technical: safelyParseKeywords(uniqueTechnicalSkills),
        soft: safelyParseKeywords(uniqueSoftSkills),
      },
    };
  } catch (error) {
    console.error("Error al obtener las habilidades:", error);
    return {
      isValid: false,
      error: "Error al obtener las habilidades",
    };
  }
};
