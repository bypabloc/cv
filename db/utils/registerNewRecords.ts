import { db, inArray, and } from "astro:db";

import { checkDuplicateKeys } from "./checkDuplicateKeys";

// Función para registrar nuevos registros en la base de datos
export const registerNewRecords = async (
  tableModel,
  keyField,
  recordsArray
) => {
  try {
    // Extraer valores de clave únicos del array de objetos
    const keys = recordsArray.map((record) => record[keyField]);

    const duplicates = checkDuplicateKeys(recordsArray, keyField);
    if (Object.keys(duplicates).length > 0) {
      console.error(
        `Duplicate keys found in records: ${JSON.stringify(duplicates)}`
      );
      throw new Error("Duplicate keys found in records");
    }

    // Verificar registros existentes
    const existingRecords = await db
      .select()
      .from(tableModel)
      .where(and(inArray(tableModel[keyField], keys)));

    // Obtener valores de claves únicas que ya existen
    const existingKeys = new Set(
      existingRecords.map((record) => record[keyField])
    );

    // Filtrar registros que no están ya registrados
    const newRecords = recordsArray.filter(
      (record) => !existingKeys.has(record[keyField])
    );

    // Si hay nuevos registros, hacer un insert en batch
    if (newRecords.length > 0) {
      const listQueries = [];
      for (const record of newRecords) {
        listQueries.push(db.insert(tableModel).values(record));
      }
      await db.batch(listQueries);
    }

    // Devolver los registros ya existentes junto con los recién insertados
    const allRegisteredRecords = await db
      .select()
      .from(tableModel)
      .where(and(inArray(tableModel[keyField], keys)));

    return allRegisteredRecords;
  } catch (error) {
    console.error("Error with Astro DB:", error);
    // console.error("recordsArray", recordsArray);
    throw new Error("Failed to register new records in Astro DB");
  }
};
