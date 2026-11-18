import { expect, test } from "@playwright/test";

// Smoke test del flujo de autenticacion. Asume el stack levantado y las
// credenciales seed (ver backend/app/db/seed.py).
test("login de mesero redirige al tablero de mesas", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: /ingreso/i })).toBeVisible();

  await page.getByLabel("Email").fill("mesero@posbar.com");
  await page.getByLabel("Password").fill("mesero12345");
  await page.getByRole("button", { name: /ingresar/i }).click();

  await page.waitForURL(/\/tables/);
  await expect(page.getByRole("heading", { name: /mesas/i })).toBeVisible();
});
