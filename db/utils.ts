import { db, inArray, and } from "astro:db";

// Función para registrar nuevos registros en la base de datos
export const registerNewRecords = async (tableModel, keyField, records) => {
  // Extraer valores de clave únicos
  const keys = Object.keys(records);

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
  const newRecords = keys
    .filter((key) => !existingKeys.has(key))
    .map((key) => ({
      ...records[key],
      [keyField]: key,
    }));

  // Insertar los nuevos registros
  if (newRecords.length > 0) {
    await db.insert(tableModel).values(newRecords);
  }

  // Devolver los registros ya existentes junto con los recién insertados
  const allRegisteredRecords = await db
    .select()
    .from(tableModel)
    .where(and(inArray(tableModel[keyField], keys)));

  return allRegisteredRecords;
};
