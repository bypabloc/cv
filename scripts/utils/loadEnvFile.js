import fs from 'fs/promises';


const loadEnvFile = async (
  {
    path = './',
    env = process.env.ENV
  } = {}
) => {
  if (!env) {
    console.error('No se ha definido la variable de entorno ENV')
    return
  }

  const filePath = `${path}/.env${env ? `.${env}` : ''}`;

  try {
    // Verificar si el archivo existe
    await fs.access(filePath);
  } catch (error) {
    console.error('El archivo especificado no existe:', filePath);
    return {}; // Devolver un objeto vacío si el archivo no existe
  }

  const oldEnv = { ...process.env };

  try {
    process.loadEnvFile(`${path}/.env.${env}`)
  } catch (error) {
    console.error('Error al cargar el archivo .env', error)
    return {}
  }

  // Extraer las nuevas variables de entorno
  const newVars = {};
  for (const key in process.env) {
      if (process.env[key] !== oldEnv[key]) {
          newVars[key] = process.env[key];
      }
  }

  // Restaurar las variables de entorno originales
  process.env = {
      ...oldEnv,
      ...newVars,
  }

  newVars.ENV = env;

  return newVars;
}

export default loadEnvFile;
