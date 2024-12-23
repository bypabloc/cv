import {
  db,
  eq,
  Users,
  UsersAttributes,
  AttributesTypes,
  Translations,
  Languages,
  sql,
} from "astro:db";

/**
 * Consulta que devuelve todos los atributos de un usuario basado en su username, incluyendo las traducciones.
 * @param {string} username - Nombre de usuario para filtrar.
 * @param {string} [languageCode="es"] - Código del idioma para las traducciones.
 * @returns {Promise<object>} - Un objeto con los atributos del usuario.
 */
export async function getAttributesByUsername(
  username: string,
  languageCode: string = "es"
) {
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

    // Obtener el userId correspondiente al username
    const users = await db
      .select()
      .from(Users)
      .where(eq(Users.username, username))
      .execute();

    // Si el usuario no se encuentra, devolver un array vacío o manejarlo según sea necesario
    if (!users.length) {
      return {
        isValid: false,
        message: "Usuario no encontrado",
      };
    }

    const user = users[0]; // Obtener el primer usuario (ya que solo debería haber uno)

    // Unir la tabla de UsersAttributes con AttributesTypes para obtener el nombre del tipo y las traducciones
    const attributes = await db
      .select({
        value: sql`COALESCE(
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

    // Crear un objeto con los nombres como claves y valores de los atributos
    const attributesObject = attributes.reduce((obj, attr) => {
      obj[attr.codeName] = {
        value: attr.attributeValue,
        type: attr.type,
        name: attr.name,
      };
      return obj;
    }, {});

    return {
      isValid: true,
      attributes: attributesObject,
    };
  } catch (error) {
    throw error; // Rethrow para manejar el error en el nivel superior
  }
}
