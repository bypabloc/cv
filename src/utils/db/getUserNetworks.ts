import { db, eq, Networks, NetworksUsers } from "astro:db";

/**
 * Replaces template placeholders with values from a given object, supporting nested properties.
 *
 * @param {string} template - The template string with placeholders and JavaScript-style template literals.
 * @param {object} context - Object containing the keys and values to replace in the template.
 * @returns {string} - The template with values substituted in place of placeholders.
 */
function replaceTemplateValues(template, context) {
  return template.replace(/{([^}]+)}/g, (_, path) => {
    const keys = path.split('.');
    let result = context;
    for (const key of keys) {
      result = result[key] || '';
    }
    return result;
  }).replace(/\$\{([^}]+)\}/g, (_, expression) => {
    try {
      // Create a new function and execute it with the context
      return Function('context', `with(context) { return ${expression}; }`)(context);
    } catch (error) {
      console.error('Error evaluating template:', error);
      return '';
    }
  });
}

/**
 * Consulta que devuelve todas las redes a las que pertenece un usuario basado en su ID de usuario.
 *
 * @param {string} userId - ID del usuario para filtrar las redes asociadas.
 * @returns {Promise<object>} - Un objeto con las redes del usuario.
 */
export const getUserNetworks = async (
  user,
  attributes: object = {}
): Promise<ResponseFunction> => {
  try {
    const networksItems = await db
      .select({
        id: Networks.id,
        codeName: Networks.codeName,
        name: Networks.name,
        url: Networks.url,
        status: Networks.status,
        config: Networks.config,
        contactInfo: NetworksUsers.contactInfo,
        NetworksUsers: NetworksUsers,
      })
      .from(Networks)
      .innerJoin(NetworksUsers, eq(Networks.id, NetworksUsers.networkId))
      .where(eq(NetworksUsers.userId, user.id))
      .execute();

    if (!networksItems.length) {
      console.error("No se encontraron redes asociadas con el usuario");
      return {
        isValid: false,
        message: "No se encontraron redes asociadas",
      };
    }

    const networks = networksItems.map((network) => {
      const NetworksUsers = network.NetworksUsers;

      const keys = {
        webUrl: "",
        printUrl: {},
        description: "",
      };
      keys.webUrl = NetworksUsers.url
        ? NetworksUsers.url
        : replaceTemplateValues(network.config.web.template, {
            url: network.url,
            contactInfo: network.contactInfo,
          });
      keys.printUrl = !network.config.print.visible
        ? {}
        : {
            url: replaceTemplateValues(network.config.print.template, {
              url: network.url,
              contactInfo: network.contactInfo,
            }),
            link: network.config.print.link,
          };
      keys.description = replaceTemplateValues(network.config.description, {
        attributes,
        network,
        name: network.name,
      });

      const icons = formatIcons(network.config.icon);

      delete network.config;
      delete network.contactInfo;
      delete network.NetworksUsers;

      return {
        ...network,
        ...keys,
        icons,
      };
    });

    return {
      isValid: true,
      data: {
        networks,
      },
    };
  } catch (error) {
    console.error("Error al obtener las redes del usuario:", error);
    throw error;
  }
};

/**
 * Helper function to format icons based on the icon configuration
 * @param {object} iconsConfig - Icon configuration from network's config
 * @returns {string[]} - Formatted icon array
 */
function formatIcons(iconsConfig) {
  return Object.entries(iconsConfig).map(([key, value]) => {
    return key === "default" ? value : `${key}:${value}`;
  });
}
