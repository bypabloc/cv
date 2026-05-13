import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig, devices } from '@playwright/test'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
void __dirname // reservado para futuras rutas absolutas

const isCI = !!process.env.CI
const PROXY_PORT = process.env.PROXY_PORT ?? '9970'
const BASE_URL = `http://localhost:${PROXY_PORT}`

export default defineConfig({
  testDir: '.',
  testMatch: '**/*.spec.ts',
  testIgnore: ['**/node_modules/**', 'fixtures/**', 'helpers/**'],
  outputDir: './results',

  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  workers: isCI ? 4 : undefined,

  timeout: 60_000,
  expect: { timeout: 10_000 },

  reporter: isCI
    ? [
        ['github'],
        ['blob', { outputDir: './blob-report' }],
        ['html', { outputFolder: './report', open: 'never' }],
        ['json', { outputFile: './results/results.json' }],
      ]
    : [['list'], ['html', { outputFolder: './report', open: 'never' }]],

  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: isCI ? 'retain-on-failure' : 'off',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    testIdAttribute: 'data-testid',
  },

  projects: [
    {
      name: 'desktop-chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'desktop-webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chromium',
      use: { ...devices['iPhone 14'], defaultBrowserType: 'chromium' },
    },
    {
      name: 'mobile-webkit',
      use: { ...devices['iPhone 14'] },
    },
    {
      name: 'tablet-chromium',
      use: { ...devices['iPad Mini'], defaultBrowserType: 'chromium' },
    },
  ],
})
