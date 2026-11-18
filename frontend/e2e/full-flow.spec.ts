import { expect, test, type Page } from "@playwright/test";

// Flujo end-to-end completo (scope PDR): login -> catalogo -> mesa -> orden -> pago -> corte.
// Requiere el stack levantado y las credenciales seed del backend.
//
// Los nombres y el numero de mesa se generan por corrida para que el test sea
// idempotente: se puede repetir sin chocar con los datos de corridas previas.

/** Sufijo unico por corrida (categorias/productos). */
const runId = Date.now().toString(36);

/** Numero de mesa libre (el backend solo admite 1..999). */
async function freeTableNumber(page: Page): Promise<number> {
  const response = await page.request.get("/api/v1/tables");
  expect(response.ok()).toBeTruthy();
  const tables = (await response.json()) as { table_number: number }[];
  const used = new Set(tables.map((table) => table.table_number));
  for (let number = 1; number <= 999; number += 1) {
    if (!used.has(number)) return number;
  }
  throw new Error("no hay numeros de mesa libres (1..999)");
}

const categoryName = `Cerveza ${runId}`;
const productName = `Hamburguesa ${runId}`;

test("flujo completo: catalogo, orden, pago y corte", async ({ page }) => {
  // --- Login (admin) ---
  await page.goto("/login");
  await page.getByLabel("Email").fill("admin@posbar.com");
  await page.getByLabel("Password").fill("admin12345");
  await page.getByRole("button", { name: /ingresar/i }).click();
  await page.waitForURL("/tables");

  const tableNumber = await freeTableNumber(page);

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
  await expect(
    page.getByText(new RegExp(`^Mesa ${tableNumber}\\b`)),
  ).toBeVisible();

  // --- Abrir orden en la mesa ---
  await page.goto("/tables");
  // Clic en la tarjeta completa. Con emulacion movil, Playwright calcula mal
  // el viewport visual y el auto-scroll deja el centro bajo otra tarjeta.
  await page
    .getByRole("link")
    .filter({ has: page.getByText(`Mesa ${tableNumber}`, { exact: true }) })
    .click({ force: true });
  await page.getByRole("button", { name: "Abrir orden" }).click();

  // --- Agregar el producto ---
  const productSelect = page.getByLabel("Producto");
  const optionValue = await productSelect
    .locator("option", { hasText: productName })
    .getAttribute("value");
  expect(optionValue).toBeTruthy();
  await productSelect.selectOption(optionValue as string);
  await page.getByRole("button", { name: "Agregar" }).click();
  await expect(page.getByText(productName).first()).toBeVisible();

  // --- Pagar total ---
  await page.getByRole("button", { name: /pagar total/i }).click({ force: true });
  // Tras pagar, el badge muestra el estado real de la orden.
  await expect(page.getByText("paid")).toBeVisible();

  // --- Corte del dia ---
  await page.goto("/report");
  await expect(page.getByText("Corte del dia")).toBeVisible();
  await expect(page.getByText("Total vendido")).toBeVisible();
});

test("login mesero y ver dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("mesero@posbar.com");
  await page.getByLabel("Password").fill("mesero12345");
  await page.getByRole("button", { name: /ingresar/i }).click();
  await page.waitForURL("/tables");
  await expect(page.getByRole("heading", { name: /mesas/i })).toBeVisible();
});

test("dos sesiones ven el cambio de mesa en vivo (WebSocket)", async ({
  browser,
}) => {
  // Dos contextos aislados = dos sesiones con cookies distintas.
  const adminContext = await browser.newContext();
  const waiterContext = await browser.newContext();
  const admin = await adminContext.newPage();
  const waiter = await waiterContext.newPage();

  try {
    await admin.goto("/login");
    await admin.getByLabel("Email").fill("admin@posbar.com");
    await admin.getByLabel("Password").fill("admin12345");
    await admin.getByRole("button", { name: /ingresar/i }).click();
    await admin.waitForURL("/tables");

    const tableNumber = await freeTableNumber(admin);

    await waiter.goto("/login");
    await waiter.getByLabel("Email").fill("mesero@posbar.com");
    await waiter.getByLabel("Password").fill("mesero12345");
    await waiter.getByRole("button", { name: /ingresar/i }).click();
    await waiter.waitForURL("/tables");

    // Mesa nueva via API (la cookie de admin viaja en la APIRequestContext).
    const created = await admin.request.post("/api/v1/tables", {
      data: { table_number: tableNumber },
    });
    expect(created.ok()).toBeTruthy();

    // El admin deja abierto el tablero; no lo recarga durante el test.
    await admin.goto("/tables");
    const adminCard = admin.getByRole("link").filter({
      has: admin.getByText(`Mesa ${tableNumber}`, { exact: true }),
    });
    await expect(adminCard).toContainText("Libre");

    // El mesero abre la orden en otra sesion.
    await waiter.goto("/tables");
    await waiter
      .getByRole("link")
      .filter({ has: waiter.getByText(`Mesa ${tableNumber}`, { exact: true }) })
      .click({ force: true });
    await waiter.getByRole("button", { name: "Abrir orden" }).click();
    await expect(waiter.getByText("open")).toBeVisible();

    // El tablero del admin se actualiza solo, por el WebSocket.
    await expect(adminCard).toContainText("Ocupada", { timeout: 15_000 });
  } finally {
    await adminContext.close();
    await waiterContext.close();
  }
});
