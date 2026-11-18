import type { DailyReport } from "@/lib/types";

/** Escapa un campo CSV (comillas dobles si contiene separadores o comillas). */
function escapeField(value: string | number): string {
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/** Convierte el corte del dia en CSV (montos en pesos enteros). */
export function dailyReportToCsv(report: DailyReport): string {
  const rows: (string | number)[][] = [
    ["Fecha", report.date],
    ["Total vendido", report.total],
    [],
    ["Por mesa", ""],
    ["Mesa", "Total"],
    ...report.by_table.map((row) => [`Mesa ${row.table_number}`, row.total]),
    [],
    ["Por producto", "", ""],
    ["Producto", "Cantidad", "Ingresos"],
    ...report.by_product.map((row) => [row.name, row.qty, row.revenue]),
  ];
  return rows.map((row) => row.map(escapeField).join(",")).join("\n");
}

/** Descarga un CSV con BOM para que Excel respete los acentos. */
export function downloadCsv(filename: string, csv: string): void {
  const blob = new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
