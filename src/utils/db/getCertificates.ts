import { db, eq, Certificates, Issuers, sql } from "astro:db";

/**
 * Consulta que devuelve todos los certificados.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta.
 */
export const getCertificates = async ({
  status,
  user,
}: {
  status?: string;
  user: { id: string };
}): Promise<ResponseFunction> => {
  try {
    let query = db
      .select({
        id: Certificates.id,
        issuer: Issuers,
        title: Certificates.title,
        date: Certificates.date,
        url: Certificates.url,
      })
      .from(Certificates)
      .leftJoin(Issuers, eq(Issuers.id, Certificates.issuerId))
      .where(eq(Certificates.userId, user.id));

    if (status) {
      query = query.where(eq(Certificates.status, status));
    }

    const certificates = await query.execute();

    // console.log(
    //   "Certificados obtenidos correctamente",
    //   JSON.stringify(certificates, null, 2)
    // );

    return {
      isValid: true,
      data: {
        certificates,
      },
    };
  } catch (error) {
    console.error("Error al obtener las experiencias educativas:", error);
    return {
      isValid: false,
      error: "Error al obtener las experiencias educativas",
    };
  }
};
