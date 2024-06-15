import { defineConfig } from 'astro/config';
import unocss from '@unocss/astro';
import vue from '@astrojs/vue';
import db from "@astrojs/db";
import node from "@astrojs/node";

import sitemap from "@astrojs/sitemap";

// https://astro.build/config
export default defineConfig({
  site: process.env.BASE_URL || "http://localhost:4321",
  vite: {
    define: {
      'process.env': {}
    },
    plugins: []
  },
  integrations: [
    unocss({
      configFilePath: './unocss.config.ts'
    }),
    vue(),
    db(),
    sitemap(),
  ],
  output: 'hybrid',
  adapter: node({
    mode: "standalone"
  })
});