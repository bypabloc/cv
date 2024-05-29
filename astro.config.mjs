import { defineConfig } from 'astro/config';
import unocss from '@unocss/astro';
import vue from '@astrojs/vue';
import db from "@astrojs/db";
import node from "@astrojs/node";

// https://astro.build/config
export default defineConfig({
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
  ],
  i18n: {
    defaultLocale: "es",
    locales: ["es", "en"],
    routing: {
        prefixDefaultLocale: false
    },
    fallback: {
        "es": "en",
        "en": "es",
    },
  },
  output: 'hybrid',
  adapter: node({
    mode: "standalone"
  })
});
