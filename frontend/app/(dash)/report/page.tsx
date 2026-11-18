"use client";

import { useQuery } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/input";
import { reportsApi } from "@/lib/api";
import { dailyReportToCsv, downloadCsv } from "@/lib/csv";
import { formatCOP, todayBogota } from "@/lib/utils";

export default function ReportPage() {
  const [date, setDate] = useState(todayBogota());
  const { data, isLoading, isError } = useQuery({
    queryKey: ["report", date],
    queryFn: () => reportsApi.daily(date),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <h1 className="text-lg font-semibold">Corte del dia</h1>
        <div className="flex items-end gap-2">
          <div className="flex flex-col gap-1">
            <Label htmlFor="date">Fecha</Label>
            <Input
              id="date"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-44"
            />
          </div>
          <Button
            variant="outline"
            disabled={!data}
            onClick={() =>
              data && downloadCsv(`corte-${data.date}.csv`, dailyReportToCsv(data))
            }
          >
            <Download className="h-4 w-4" /> Exportar CSV
          </Button>
        </div>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Cargando...</p>}

      {isError && (
        <p className="rounded bg-red-50 p-2 text-sm text-red-600">
          No se pudo cargar el corte. Intenta de nuevo.
        </p>
      )}

      {data && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Total vendido</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{formatCOP(data.total)}</p>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Por mesa</CardTitle>
              </CardHeader>
              <CardContent>
                <table className="w-full text-sm">
                  <tbody>
                    {data.by_table.map((row) => (
                      <tr
                        key={row.table_number}
                        className="border-b border-slate-100"
                      >
                        <td className="py-1.5">Mesa {row.table_number}</td>
                        <td className="py-1.5 text-right">
                          {formatCOP(row.total)}
                        </td>
                      </tr>
                    ))}
                    {data.by_table.length === 0 && (
                      <tr>
                        <td className="py-2 text-slate-500">Sin ventas.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Por producto</CardTitle>
              </CardHeader>
              <CardContent>
                <table className="w-full text-sm">
                  <tbody>
                    {data.by_product.map((row) => (
                      <tr key={row.name} className="border-b border-slate-100">
                        <td className="py-1.5">{row.name}</td>
                        <td className="py-1.5 text-center text-slate-500">
                          {row.qty}
                        </td>
                        <td className="py-1.5 text-right">
                          {formatCOP(row.revenue)}
                        </td>
                      </tr>
                    ))}
                    {data.by_product.length === 0 && (
                      <tr>
                        <td className="py-2 text-slate-500">Sin ventas.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
