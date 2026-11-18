import { describe, expect, it } from "vitest";

import { dailyReportToCsv } from "@/lib/csv";

const report = {
  date: "2026-11-17",
  total: 15000,
  by_table: [{ table_number: 1, total: 15000 }],
  by_product: [{ name: "Cerveza, fria", qty: 3, revenue: 15000 }],
};

describe("dailyReportToCsv", () => {
  it("incluye totales, mesas y productos", () => {
    const csv = dailyReportToCsv(report);
    expect(csv).toContain("Fecha,2026-11-17");
    expect(csv).toContain("Total vendido,15000");
    expect(csv).toContain("Mesa 1,15000");
    expect(csv).toContain("Cantidad,Ingresos");
  });

  it("escapa comas dentro de los nombres", () => {
    expect(dailyReportToCsv(report)).toContain('"Cerveza, fria",3,15000');
  });
});
