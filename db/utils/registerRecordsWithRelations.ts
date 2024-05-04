import { db, eq, inArray } from "astro:db";

/**
 * Función para registrar registros con relaciones.
 *
 * @param {Object} tableModel - Modelo de la tabla a registrar.
 * @param {Array} recordsArray - Array de registros con relaciones.
 * @param {Object} tables - Objeto que contiene las tablas para las relaciones.
 * @param {String} [keyField] - Campo único opcional para verificar duplicados.
 */
export const registerRecordsWithRelations = async (
  tableModel: any,
  recordsArray: Record<string, any>[],
  tables: Record<string, any>,
  keyField = null
) => {
  try {
    const processedRecords = [];

    for (const record of recordsArray) {
      const { relationship, ...otherFields } = record;
      const processedRecord = { ...otherFields };

      for (const [relationKey, relationInfo] of Object.entries(relationship)) {
        const { table, field, value } = relationInfo;
        const relatedTable = tables[table];

        if (!relatedTable) {
          throw new Error(`Table ${table} not found in tables.`);
        }

        console.log("relatedTable.model[field]", relatedTable.model[field]);

        const relatedRecords = await db
          .select()
          .from(relatedTable.model)
          .where(eq(relatedTable.model[field], value));

        const relatedRecord = relatedRecords?.[0]; // Obtener el primer registro, si existe

        if (!relatedRecord) {
          throw new Error(
            `No record found in table ${table} for ${field} = ${value}`
          );
        }

        console.log("relatedRecord", relatedRecord);

        processedRecord[relationKey] = relatedRecord.uuid;
      }

      processedRecords.push(processedRecord);
    }

    if (keyField) {
      const keys = processedRecords.map((record) => record[keyField]);
      const existingRecords = await db
        .select()
        .from(tableModel)
        .where(inArray(tableModel[keyField], keys))
        .execute(); // Modificado para usar `.execute()` para obtener todos los registros

      const existingKeys = new Set(
        existingRecords.map((record) => record[keyField])
      );

      // Filtrar registros que no están ya registrados
      const newRecords = processedRecords.filter(
        (record) => !existingKeys.has(record[keyField])
      );

      // Insertar los nuevos registros
      if (newRecords.length > 0) {
        await db.insert(tableModel).values(newRecords).execute();
      }

      return [...existingRecords, ...newRecords];
    } else {
      // Insertar los registros procesados
      if (processedRecords.length > 0) {
        console.log("processedRecords", processedRecords);
        await db.insert(tableModel).values(processedRecords);
      }

      return processedRecords;
    }
  } catch (error) {
    console.error("Error with Astro DB:", error);
    throw new Error("Failed to register records with relations in Astro DB");
  }
};
