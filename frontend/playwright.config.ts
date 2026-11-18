import { defineConfig, devices } from "@playwright/test";

// Tests end-to-end. Requieren el stack levantado (frontend + backend + db):
//   docker compose -f infra/docker-compose.yml up --build
//   npx playwright install   # una sola vez (descarga navegadores)
//   npm run e2e
export default defineConfig({
  testDir: "./e2e",
  // Los tests comparten la BD y crean mesas (numero unico 1..999): se ejecutan
  // en serie para que no compitan por el mismo numero.
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
