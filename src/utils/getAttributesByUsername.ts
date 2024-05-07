import { db, eq, Users, UsersAttributes } from "astro:db";

/**
 * Consulta que devuelve todos los atributos de un usuario basado en su username.
 * @param {string} username - Nombre de usuario para filtrar.
 * @returns {Promise<UsersAttributes[]>} - Una lista de atributos del usuario.
 */
export async function getAttributesByUsername(username: string) {
  try {
    // Obtener el userId correspondiente al username
    const users = await db
      .select()
      .from(Users)
      .where(eq(Users.columns.username, username))
      .execute(); // `.first()` para obtener el primer resultado

    // Si el usuario no se encuentra, devolver un array vacío o manejarlo según sea necesario
    if (!users.length) {
      console.error("Usuario no encontrado");
      return [];
    }

    const user = users[0]; // Obtener el primer usuario (ya que solo debería haber uno)

    // Obtener los atributos del usuario usando el userId
    const attributes = await db
      .select()
      .from(UsersAttributes)
      .where(eq(UsersAttributes.columns.userId, user.id))
      .all(); // `.all()` para obtener todos los resultados como un array

    return attributes;
  } catch (error) {
    console.error("Error al obtener los atributos del usuario:", error);
    throw error; // Rethrow para manejar el error en el nivel superior
  }
}
