import fsExtra from 'fs-extra';
import { execSync } from 'child_process';
import path from 'path';
import { BaseClass } from "./utils/baseClass.js";

const { copySync, removeSync, ensureDirSync } = fsExtra;

export class MergeBuild extends BaseClass {
  constructor() {
    super();
    this.rootDir = process.cwd();
    this.distDir = path.join(this.rootDir, 'dist/client');
    this.tmpDir = path.join(this.rootDir, '.tmp');
  }

  async execute() {
    try {
      // Ejecutar el comando de build
      console.log('Running build...');
      execSync('pnpm run build:no-check', { stdio: 'inherit' });

      // Preparar el directorio tmp
      console.log('Preparing .tmp directory...');
      if (fsExtra.existsSync(this.tmpDir)) {
        removeSync(this.tmpDir);
      }
      ensureDirSync(this.tmpDir);

      // Copiar contenido de dist/client a tmp
      console.log('Copying files to .tmp directory...');
      copySync(this.distDir, this.tmpDir);
      console.log('Files copied successfully.');

    } catch (error) {
      console.error('Error during build or file operations:', error);
    }
  }
}

const mergeBuild = new MergeBuild();
mergeBuild.execute();
