import { expect, test } from "@playwright/test";

// Flujo end-to-end completo (scope PDR): login → catalogo → mesa → orden → pago → corte.
// Requiere el stack levantado y las credenciales seed del backend.
test("flujo completo: catalogo, orden, pago y corte", async ({ page }) => {
  // Use static names to avoid timestamp-dependent flakiness
  const categoryName = "Cerveza Artesanal";
  const productName = "Hamburguesa";
  const tableNumber = 5;

  // --- Login (admin) ---
  await page.goto("/login");
  await page.getByLabel("Email").fill("admin@posbar.com");
  await page.getByLabel("Password").fill("admin12345");
  await page.getByRole("button", { name: /ingresar/i }).click();
  await page.waitForURL("/tables");

  // --- Admin: crear categoria ---
  await page.goto("/admin");
  await page.getByPlaceholder("Nombre").fill(categoryName);
  await page.getByRole("button", { name: "Agregar" }).click();
  await expect(page.getByText(categoryName)).toBeVisible();

  // --- Admin: crear producto ---
  await page.getByRole("button", { name: "Productos" }).click();
  await page.getByPlaceholder("Nombre").fill(productName);
  await page.getByRole("combobox").selectOption({ label: categoryName });
  await page.getByPlaceholder("Precio").fill("5000");
  await page.getByRole("button", { name: "Agregar" }).click();
  await expect(page.getByText(productName)).toBeVisible();

  // --- Admin: crear mesa ---
  await page.getByRole("button", { name: "Mesas" }).click();
  await page.getByPlaceholder("Numero").fill(String(tableNumber));
  await page.getByRole("button", { name: "Agregar" }).click();
  await expect(page.getByText(`Mesa ${tableNumber}`)).toBeVisible();

  // --- Abrir orden en la mesa ---
  await page.goto("/tables");
  await page.getByText(`Mesa ${tableNumber}`).click();
  await page.getByRole("button", { name: "Abrir orden" }).click();

  // --- Agregar el producto ---
  await page.getByRole("combobox").first().selectOption(productName);
  await page.getByRole("button", { name: "Agregar" }).click();
  await expect(page.getByText(productName).first()).toBeVisible();

  // --- Pagar total ---
  await page.getByRole("button", { name: /pagar total/i }).click();
  // After paying, the status badge should show "paid"
  await expect(page.getByText("paid")).toBeVisible();

  // --- Corte del dia ---
  await page.goto("/report");
  await expect(page.getByText("Corte del dia")).toBeVisible();
  await expect(page.getByText("Total vendido")).toBeVisible();
});

// Nuevo test: login mesero + verificación básica
test("login mesero y ver dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("mesero@posbar.com");
  await page.getByLabel("Password").fill("mesero12345");
  await page.getByRole("button", { name: /ingresar/i }).click();
  await page.waitForURL("/tables");
  await expect(page.getByRole("heading", { name: /mesas/i })).toBeVisible();
});