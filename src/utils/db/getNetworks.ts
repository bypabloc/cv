import { db, eq, Networks } from "astro:db";

/**
 * Consulta que devuelve todos las redes.
 * @param {string} status - Estado del usuario para filtrar.
 * @returns {Promise<object>} - Lista de redes.
 */
export const getNetworks = async ({
  status,
}: {
  status?: string;
} = {}): Promise<object> => {
  try {
    let networks = await db.select().from(Networks).execute();

    if (status) {
      networks = networks.where(eq(Networks.status, status));
    }

    if (!networks.length) {
      console.error("Usuario no encontrado");
      return {
        isValid: false,
        error: "Usuario no encontrado",
      };
    }

    return {
      isValid: true,
      data: {
        networks,
      },
    };
  } catch (error) {
    console.error("Error al obtener los atributos del usuario:", error);
    throw error; // Rethrow para manejar el error en el nivel superior
  }
};
