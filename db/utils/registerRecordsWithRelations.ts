import { db, eq, and, inArray } from "astro:db";

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

      // for (const [field, value] of Object.entries(processedRecord)) {
      //   const columnType = tableModel[field]?.columnType;
      //   if (
      //     columnType === "SQLiteCustomColumn" &&
      //     tableModel[field]?.sqlName === "text"
      //   ) {
      //     processedRecord[field] = value ? new Date(value) : null;
      //   }
      // }

      for (const [relationKey, relationInfo] of Object.entries(
        relationship || {}
      )) {
        const { table, field, value } = relationInfo;
        const relatedTable = tables[table];

        if (!relatedTable) {
          throw new Error(`Table ${table} not found in tables.`);
        }

        const relatedRecords = await db
          .select()
          .from(relatedTable.model)
          .where(eq(relatedTable.model[field], value))
          .execute();

        const relatedRecord = relatedRecords?.[0]; // Obtener el primer registro, si existe

        if (!relatedRecord) {
          throw new Error(
            `No record found in table ${table} for ${field} = ${value}`
          );
        }

        processedRecord[relationKey] = relatedRecord.id;
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
      const result = [];
      // Insertar los registros procesados
      if (processedRecords.length > 0) {
        for (const record of processedRecords) {
          try {
            let existingRecord = null;
            const uniqueColumns = Object.keys(tableModel).filter(
              (key) => tableModel[key].isUnique
            );
            if (uniqueColumns.length > 0) {
              let query = db.select().from(tableModel);
              for (const column of uniqueColumns) {
                if (record[column]) {
                  query = query.where(and(tableModel[column], record[column]));
                }
              }
              const records = await query.execute();
              existingRecord = records.length ? records[0] : null;
            }

            if (existingRecord) {
              result.push(existingRecord);
              continue;
            }

            if (Object.keys(record).length > 0) {
              let query = db.select().from(tableModel);
              const listVerify = [];
              for (const column of Object.keys(record)) {
                if (column === "id") continue;
                query = query.where(and(tableModel[column], record[column]));
                listVerify.push({
                  column: column,
                  data: record[column],
                });
              }
              console.log(
                `listVerify > ${tableModel[Symbol.for("drizzle:Name")]}`,
                listVerify
              );
              const records = await query.execute();
              existingRecord = records.length ? records[0] : null;
              console.log("existingRecord", existingRecord);
            }

            if (existingRecord) {
              result.push(existingRecord);
              continue;
            }

            try {
              console.log("record to insert:", JSON.stringify(record, null, 2));
              const insertedRecords = await db
                .insert(tableModel)
                .values(record)
                .returning()
                .execute();
              result.push(...insertedRecords);
            } catch (error) {
              console.error("Error inserting records:", error);
              console.error("tableModel", tableModel);
              throw new Error("Failed to insert records in Astro DB");
            }
          } catch (error) {
            console.error("Error inserting records:", error);
            throw new Error("Failed to insert records in Astro DB");
          }
        }
      }

      return result;
    }
  } catch (error) {
    console.error("Error with Astro DB:", error);
    throw new Error("Failed to register records with relations in Astro DB");
  }
};
