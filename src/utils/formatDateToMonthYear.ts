// Función para formatear la fecha a YYYY-MM
export function formatDateToMonthYear(dateString) {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0"); // Añade un cero inicial si es necesario
  return `${year} - ${month}`;
}
