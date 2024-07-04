import { defineConfig } from 'astro/config';
import unocss from '@unocss/astro';
import vue from '@astrojs/vue';
import db from "@astrojs/db";
import node from "@astrojs/node";
import Unlighthouse from '@unlighthouse/vite'
import sitemap from "@astrojs/sitemap";

// https://astro.build/config
export default defineConfig({
  site: process.env.BASE_URL || "http://localhost:4321",
  vite: {
    define: {
      'process.env': {}
    },
    plugins: [
      Unlighthouse({
        // config
      })
    ]
  },
  integrations: [
    unocss({
      configFilePath: './unocss.config.ts'
    }),
    vue(),
    db({
      name: '@astrojs/db',
      options: {
        token: process.env.ASTRO_DB_API_TOKEN,
      },
    }),
    sitemap(),
  ],
  output: 'hybrid',
  adapter: node({
    mode: "standalone"
  })
});