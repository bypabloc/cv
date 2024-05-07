import { defineConfig } from 'astro/config';
import unocss from '@unocss/astro';
import vue from '@astrojs/vue';
import db from "@astrojs/db";
import node from "@astrojs/node";

// https://astro.build/config
export default defineConfig({
  integrations: [
    unocss({
      configFilePath: './unocss.config.ts'
    }),
    vue(),
    db(),
  ],
  output: 'hybrid',
  adapter: node({
    mode: "standalone"
  })
});