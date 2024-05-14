import { db, eq, TypeFiles, GroupsFiles, Files, Users } from "astro:db";

/**
 * Consulta que devuelve todos los archivos de un usuario basado en su ID de usuario.
 *
 * @param {string} user - Instancia del usuario.
 * @returns {Promise<object>} - Un objeto con la información de los archivos.
 */
export const getFiles = async (user): Promise<ResponseFunction> => {
  try {
    const result = await db
      .select()
      .from(Files)
      .innerJoin(GroupsFiles, eq(Files.groupFileId, GroupsFiles.id))
      .innerJoin(TypeFiles, eq(Files.fileTypeId, TypeFiles.id))
      .innerJoin(Users, eq(Files.userId, Users.id))
      .where(eq(Users.id, user.id))
      .execute();

    // Organiza los datos en un formato agrupado por grupo de archivos
    const groupedFiles = {};

    result.forEach((item) => {
      const groupName = item.GroupsFiles.codeName;
      if (!groupedFiles[groupName]) {
        groupedFiles[groupName] = [];
      }

      groupedFiles[groupName].push({
        ...item.Files,
        typeInfo: {
          name: item.TypeFiles.name,
          extension: item.TypeFiles.extension,
          mime: item.TypeFiles.mime,
          tag: item.TypeFiles.tag,
          priority: item.TypeFiles.priority,
        },
      });
    });

    const sortedFiles = sortFilesWithinGroups(groupedFiles);

    const sortedFilesArray = {};
    Object.keys(sortedFiles).forEach((key) => {
      sortedFilesArray[key] = convertToObjectArray(sortedFiles[key]);
    });

    return {
      isValid: true,
      data: {
        files: sortedFilesArray,
      },
    };
  } catch (error) {
    return {
      isValid: false,
      data: {
        message: "Error al obtener los archivos.",
      },
    };
  }
};

function sortFilesWithinGroups(groupedFiles) {
  const sortedGroupFiles = {};

  // Procesar cada grupo original
  for (const [groupKey, files] of Object.entries(groupedFiles)) {
    sortedGroupFiles[groupKey] = {};

    // Agrupa los archivos por 'priority'
    files.forEach((file) => {
      const priority = file.priority;
      if (!sortedGroupFiles[groupKey][priority]) {
        sortedGroupFiles[groupKey][priority] = [];
      }
      sortedGroupFiles[groupKey][priority].push(file);
    });

    // Ordena cada subgrupo por 'typeInfo.priority' en orden descendente
    Object.keys(sortedGroupFiles[groupKey]).forEach((priority) => {
      sortedGroupFiles[groupKey][priority].sort(
        (a, b) => b.typeInfo.priority - a.typeInfo.priority
      );
    });
  }

  return sortedGroupFiles;
}

/**
 * Convierte los grupos numerados en objetos a un array ordenado.
 *
 * Esta función toma un objeto con claves numéricas y convierte estos grupos en un array,
 * ordenando los elementos según las claves numéricas de forma ascendente.
 *
 * @author Pablo Contreras.
 *
 * @since  2024/05/12.
 *
 * @param  {Object} groupedFiles Objeto con archivos agrupados y numerados por prioridad.
 *
 * @return {Array}               Array con los grupos de archivos ordenados por la clave numérica.
 */
function convertToObjectArray(groupedFiles) {
  const result = Object.entries(groupedFiles).map(([key, value]) => ({
    priority: key,
    files: value,
  }));

  // Ordena el array por la clave 'priority' que representa el número original de la clave en orden descendente
  result.sort((a, b) => parseInt(b.priority) - parseInt(a.priority));

  return result;
}
