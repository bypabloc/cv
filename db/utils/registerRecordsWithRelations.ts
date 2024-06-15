import { db, eq, sql, inArray } from "astro:db";

/**
 * Función para registrar registros con relaciones en lotes.
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

      for (const [relationKey, relationInfo] of Object.entries(
        relationship || {}
      )) {
        const { table, field, value } = relationInfo;
        const relatedTable = tables[table];

        if (!relatedTable) {
          console.error(`Table ${table} not found in tables.`);
          throw new Error(`Table ${table} not found in tables.`);
        }

        try {
          const relatedRecords = await db
            .select()
            .from(relatedTable.model)
            .where(eq(relatedTable.model[field], value))
            .execute();

          const relatedRecord = relatedRecords?.[0]; // Obtener el primer registro, si existe

          if (!relatedRecord) {
            console.error(
              `No record found in table ${table} for ${field} = ${value}`
            );
            throw new Error(
              `No record found in table ${table} for ${field} = ${value}`
            );
          }

          processedRecord[relationKey] = relatedRecord.id;
        } catch (error) {
          console.error(
            `Error fetching related record from table ${table} for ${field} = ${value}:`,
            error
          );
          throw new Error(
            `Error fetching related record from table ${table} for ${field} = ${value}`
          );
        }
      }

      // Convertir los datos según las condiciones especificadas
      Object.keys(processedRecord).forEach((key) => {
        if (
          key !== "id" &&
          key !== "responsibilitiesNProjects" &&
          key !== "achievements" &&
          key !== "highlights" &&
          key !== "scrappingRecommendation" &&
          key !== "keys" &&
          key !== "icons"
        ) {
          try {
            if (
              processedRecord[key] instanceof Date &&
              !isNaN(processedRecord[key])
            ) {
              return;
            } else if (typeof processedRecord[key] === "object") {
              processedRecord[key] = JSON.stringify(processedRecord[key]);
            } else if (typeof processedRecord[key] === "string") {
              if (processedRecord[key].match(/^\d{4}-\d{2}-\d{2}$/)) {
                processedRecord[key] = new Date(processedRecord[key]);
              }
            } else if (typeof processedRecord[key] === "undefined") {
              processedRecord[key] = null;
            } else if (processedRecord[key] === null) {
              processedRecord[key] = null;
            }
          } catch (error) {
            console.error("Error processing field:", key, error);
          }
        }
      });

      processedRecords.push(processedRecord);
    }

    if (keyField) {
      const keys = processedRecords.map((record) => record[keyField]);
      const existingRecords = await db
        .select()
        .from(tableModel)
        .where(inArray(tableModel[keyField], keys))
        .execute();

      const existingKeys = new Set(
        existingRecords.map((record) => record[keyField])
      );

      const newRecords = processedRecords.filter(
        (record) => !existingKeys.has(record[keyField])
      );

      if (newRecords.length > 0) {
        await db.insert(tableModel).values(newRecords).execute();
      }

      return [...existingRecords, ...newRecords];
    } else {
      const uniqueRecords = [];
      const existingRecordsMap = new Map();

      const uniqueColumns = Object.keys(tableModel).filter(
        (key) => tableModel[key].isUnique
      );

      if (uniqueColumns.length > 0) {
        let query = db.select().from(tableModel);
        for (const column of uniqueColumns) {
          if (processedRecords[0][column]) {
            query = query.where(
              inArray(
                tableModel[column],
                processedRecords.map((r) => r[column])
              )
            );
          }
        }
        const existingRecords = await query.execute();
        existingRecords.forEach((record) => {
          const key = uniqueColumns.map((col) => record[col]).join("-");
          existingRecordsMap.set(key, record);
        });
      }

      for (const record of processedRecords) {
        const key = uniqueColumns.map((col) => record[col]).join("-");
        if (existingRecordsMap.has(key)) {
          uniqueRecords.push(existingRecordsMap.get(key));
        } else {
          uniqueRecords.push(record);
        }
      }

      const newRecords = uniqueRecords.filter(
        (record) =>
          !existingRecordsMap.has(
            uniqueColumns.map((col) => record[col]).join("-")
          )
      );

      if (newRecords.length > 0) {
        await db.insert(tableModel).values(newRecords).execute();
      }

      return [...Array.from(existingRecordsMap.values()), ...newRecords];
    }
  } catch (error) {
    console.error("Error with Astro DB:", error);
    console.error("Table model:", tableModel);
    console.error("Records array:", recordsArray);
    throw new Error("Failed to register records with relations in Astro DB");
  }
};
