// Path: utils/getEnvVars.js

import getRootPath from './utils/getRootPath.js';

const getEnvVars = () => {
  const rootPath = getRootPath();
  return {
    ROOT_PATH: rootPath,
  };
};

export default getEnvVars;
