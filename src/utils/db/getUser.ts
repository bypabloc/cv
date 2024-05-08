import { db, eq, Users } from "astro:db";

/**
 * Consulta que devuelve todos los atributos de un usuario basado en su username.
 * @param {string} username - Nombre de usuario para filtrar.
 * @returns {Promise<object>} - Un objeto con los atributos del usuario.
 */
export const getUser = async (username: string) => {
  try {
    const users = await db
      .select()
      .from(Users)
      .where(eq(Users.username, username))
      .execute();

    if (!users.length) {
      console.error("Usuario no encontrado");
      return {
        isValid: false,
        error: "Usuario no encontrado",
      };
    }

    const user: typeof Users = users[0];

    return {
      isValid: true,
      data: {
        user: user,
      },
    };
  } catch (error) {
    console.error("Error al obtener los atributos del usuario:", error);
    throw error; // Rethrow para manejar el error en el nivel superior
  }
};
