import { db, eq, Users } from "astro:db";

/**
 * Consulta que devuelve todos los usuarios.
 * @param {string} status - Estado del usuario para filtrar.
 * @returns {Promise<object>} - Lista de usuarios.
 */
export const getUsers = async ({
  status,
}: {
  status?: string;
} = {}): Promise<object> => {
  try {
    let users = await db.select().from(Users).execute();

    if (status) {
      users = users.where(eq(Users.status, status));
    }

    if (!users.length) {
      console.error("Usuario no encontrado");
      return {
        isValid: false,
        error: "Usuario no encontrado",
      };
    }

    return {
      isValid: true,
      data: {
        users,
      },
    };
  } catch (error) {
    console.error("Error al obtener los atributos del usuario:", error);
    throw error; // Rethrow para manejar el error en el nivel superior
  }
};
