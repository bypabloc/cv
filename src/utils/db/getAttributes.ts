import { db, eq, UsersAttributes, AttributesTypes } from "astro:db";

/**
 * Consulta que devuelve todos los atributos de un usuario basado en su username.
 * @param {string} username - Nombre de usuario para filtrar.
 * @returns {Promise<object>} - Un objeto con los atributos del usuario.
 */
export const getAttributes = async (user: Record<string, any>) => {
  try {
    const attributes = await db
      .select({
        value: UsersAttributes.attributeValue,
        codeName: AttributesTypes.codeName,
        type: AttributesTypes.type,
        name: AttributesTypes.name,
      })
      .from(UsersAttributes)
      .innerJoin(
        AttributesTypes,
        eq(UsersAttributes.attributeTypeId, AttributesTypes.id)
      )
      .where(eq(UsersAttributes.userId, user.id))
      .execute();

    if (!attributes.length) {
      console.error("Atributos no encontrados");
      return {
        isValid: false,
        message: "Atributos no encontrados",
      };
    }

    const attributesObject = attributes.reduce((obj, attr) => {
      const values = {
        value: attr.value,
      };
      if (attr.type === "object") {
        values.value = JSON.parse(attr.value);
      }
      obj[attr.codeName] = values;
      return obj;
    }, {});

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
