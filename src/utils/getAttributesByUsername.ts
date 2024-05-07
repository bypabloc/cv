import { db, eq, Users, UsersAttributes, AttributesTypes } from "astro:db";

/**
 * Consulta que devuelve todos los atributos de un usuario basado en su username.
 * @param {string} username - Nombre de usuario para filtrar.
 * @returns {Promise<object>} - Un objeto con los atributos del usuario.
 */
export async function getAttributesByUsername(username: string) {
  try {
    // Obtener el userId correspondiente al username
    const users = await db
      .select()
      .from(Users)
      .where(eq(Users.username, username))
      .execute();

    // Si el usuario no se encuentra, devolver un array vacío o manejarlo según sea necesario
    if (!users.length) {
      console.error("Usuario no encontrado");
      return {
        isValid: false,
        message: "Usuario no encontrado",
      };
    }

    const user = users[0]; // Obtener el primer usuario (ya que solo debería haber uno)

    // Unir la tabla de UsersAttributes con AttributesTypes para obtener el nombre del tipo
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

    // Crear un objeto con los nombres como claves y valores de los atributos
    const attributesObject = attributes.reduce((obj, attr) => {
      obj[attr.codeName] = {
        value: attr.value,
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
    console.error("Error al obtener los atributos del usuario:", error);
    throw error; // Rethrow para manejar el error en el nivel superior
  }
}
