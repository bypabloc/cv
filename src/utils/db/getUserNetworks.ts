import { db, eq, Networks, NetworksUsers } from "astro:db";

/**
 * Consulta que devuelve todas las redes a las que pertenece un usuario basado en su ID de usuario.
 *
 * @param {string} userId - ID del usuario para filtrar las redes asociadas.
 * @returns {Promise<object>} - Un objeto con las redes del usuario.
 */
export const getUserNetworks = async (user: Record<string, any>) => {
  try {
    const networks = await db
      .select({
        id: Networks.id,
        codeName: Networks.codeName,
        name: Networks.name,
        url: Networks.url,
        status: Networks.status,
        username: NetworksUsers.username,
        networksUsersUrl: NetworksUsers.url,
      })
      .from(Networks)
      .innerJoin(NetworksUsers, eq(Networks.id, NetworksUsers.networkId))
      .where(eq(NetworksUsers.userId, user.id))
      .execute();

    if (!networks.length) {
      console.error("No se encontraron redes asociadas con el usuario");
      return {
        isValid: false,
        message: "No se encontraron redes asociadas",
      };
    }

    return {
      isValid: true,
      data: {
        networks: networks,
      },
    };
  } catch (error) {
    console.error("Error al obtener las redes del usuario:", error);
    throw error;
  }
};
