import { expect, test } from "@playwright/test";

test("exportar corte del dia a CSV", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("admin@posbar.com");
  await page.getByLabel("Password").fill("admin12345");
  await page.getByRole("button", { name: /ingresar/i }).click();
  await page.waitForURL("/tables");

  await page.goto("/report");
  const exportButton = page.getByRole("button", { name: /exportar csv/i });
  await expect(exportButton).toBeEnabled();

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    exportButton.click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/^corte-\d{4}-\d{2}-\d{2}\.csv$/);
});
