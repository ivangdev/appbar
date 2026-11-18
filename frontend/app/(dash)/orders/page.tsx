"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/input";
import { ordersApi, productsApi, tablesApi } from "@/lib/api";
import { formatCOP, todayBogota } from "@/lib/utils";

const METHOD_LABELS: Record<string, string> = {
  cash: "Efectivo",
  nequi: "Nequi",
  transfer: "Transferencia",
};

export default function OrdersHistoryPage() {
  const [date, setDate] = useState(todayBogota());
  const { data: orders = [], isLoading, isError } = useQuery({
    queryKey: ["orders-history", date],
    queryFn: () => ordersApi.history(date),
  });
  const { data: tables = [] } = useQuery({
    queryKey: ["tables"],
    queryFn: () => tablesApi.list(),
  });
  const { data: products = [] } = useQuery({
    queryKey: ["products"],
    queryFn: () => productsApi.list(),
  });

  const tableNumber = useMemo(() => {
    const map = new Map(tables.map((t) => [t.id, t.table_number]));
    return (id: string) => map.get(id) ?? "?";
  }, [tables]);

  const productName = useMemo(() => {
    const map = new Map(products.map((p) => [p.id, p.name]));
    return (id: string) => map.get(id) ?? "Producto";
  }, [products]);

  const total = orders.reduce((acc, order) => acc + order.total_amount, 0);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-lg font-semibold">Historial de ordenes</h1>
          <p className="text-sm text-slate-400">
            {orders.length} ordenes · {formatCOP(total)} en consumo
          </p>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="history-date">Fecha</Label>
          <Input
            id="history-date"
            type="date"
            value={date}
            className="w-44"
            onChange={(e) => setDate(e.target.value)}
          />
        </div>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Cargando...</p>}
      {isError && (
        <p className="rounded bg-red-50 p-2 text-sm text-red-600">
          No se pudo cargar el historial.
        </p>
      )}

      {!isLoading && orders.length === 0 && (
        <Card>
          <CardContent className="p-6 text-sm text-slate-500">
            No hay ordenes registradas para esa fecha.
          </CardContent>
        </Card>
      )}

      {orders.map((order) => (
        <Card key={order.id}>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle>Mesa {tableNumber(order.table_id)}</CardTitle>
              <div className="flex items-center gap-3">
                <span className="text-sm text-slate-500">
                  Total {formatCOP(order.total_amount)} · Pagado{" "}
                  {formatCOP(order.amount_paid)}
                </span>
                <Badge variant={order.status}>{order.status}</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <details className="group">
              <summary className="cursor-pointer text-sm text-slate-500 hover:text-slate-700">
                Ver detalle ({order.items.length} items ·{" "}
                {order.payments.length} pagos)
              </summary>
              <div className="mt-3 grid gap-4 md:grid-cols-2">
                <div>
                  <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">
                    Consumo
                  </p>
                  <ul className="flex flex-col gap-1 text-sm">
                    {order.items.map((item) => (
                      <li key={item.id} className="flex justify-between gap-2">
                        <span>
                          {item.quantity} × {productName(item.product_id)}
                          {item.notes ? (
                            <span className="text-slate-400"> · {item.notes}</span>
                          ) : null}
                        </span>
                        <span className="text-slate-500">
                          {formatCOP(item.total_price)}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">
                    Pagos
                  </p>
                  <ul className="flex flex-col gap-1 text-sm">
                    {order.payments.map((payment) => (
                      <li
                        key={payment.id}
                        className={
                          payment.cancelled_at ? "text-slate-400 line-through" : ""
                        }
                      >
                        {formatCOP(payment.amount)} ·{" "}
                        {METHOD_LABELS[payment.method] ?? payment.method}
                        {payment.cancelled_at ? " · cancelado" : ""}
                      </li>
                    ))}
                    {order.payments.length === 0 && (
                      <li className="text-slate-500">Sin pagos.</li>
                    )}
                  </ul>
                </div>
              </div>
            </details>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
