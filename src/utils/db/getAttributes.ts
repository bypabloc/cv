import {
  db,
  eq,
  UsersAttributes,
  AttributesTypes,
  Translations,
  Languages,
  sql,
} from "astro:db";

/**
 * Consulta que devuelve todos los atributos de un usuario basado en su ID, incluyendo las traducciones.
 * @param {Record<string, any>} user - Objeto del usuario para filtrar.
 * @param {string} [languageCode="es"] - Código del idioma para las traducciones.
 * @returns {Promise<ResponseFunction>} - Un objeto con los atributos del usuario.
 */
export const getAttributes = async (
  user: Record<string, any>,
  languageCode: string = "es"
): Promise<ResponseFunction> => {
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
    const attributes = await db
      .select({
        attributeValue: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${UsersAttributes.id}
             AND ${Translations.tableName} = 'UsersAttributes'
             AND ${Translations.field} = 'attributeValue'
             AND ${Translations.languageId} = ${languageId}),
          ${UsersAttributes.attributeValue}) AS attributeValue`,
        codeName: AttributesTypes.codeName,
        type: AttributesTypes.type,
        name: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${AttributesTypes.id}
             AND ${Translations.tableName} = 'AttributesTypes'
             AND ${Translations.field} = 'name'
             AND ${Translations.languageId} = ${languageId}),
          ${AttributesTypes.name}) AS name`,
      })
      .from(UsersAttributes)
      .innerJoin(
        AttributesTypes,
        eq(UsersAttributes.attributeTypeId, AttributesTypes.id)
      )
      .where(eq(UsersAttributes.userId, user.id))
      .execute();

    if (!attributes.length) {
      return {
        isValid: false,
        message: "Atributos no encontrados",
      };
    }

    const attributesObject = attributes.reduce((obj, attr) => {
      let value = attr.attributeValue;
      if (attr.type === "object" && value) {
        try {
          value = JSON.parse(value);
        } catch (e) {
          console.warn(`Error parsing JSON for attribute ${attr.codeName}:`, e);
        }
      }
      obj[attr.codeName] = { value };
      return obj;
    }, {});

    // console.log(
    //   "Atributos del usuario:",
    //   JSON.stringify(attributesObject, null, 2)
    // );

    return {
      isValid: true,
      data: {
        attributes: attributesObject,
      },
    };
  } catch (error) {
    console.error("Error al obtener los atributos del usuario:", error);
    throw error;
  }
};
