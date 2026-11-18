"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select } from "@/components/ui/input";
import {
  apiError,
  categoriesApi,
  ordersApi,
  paymentsApi,
  productsApi,
} from "@/lib/api";
import type { OrderItem, PaymentMethod } from "@/lib/types";
import { formatCOP } from "@/lib/utils";
import { useTablesSocket } from "@/hooks/use-tables-socket";

export default function OrderPage() {
  const params = useParams<{ id: string }>();
  const tableId = params.id;
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [method, setMethod] = useState<PaymentMethod>("cash");
  const [productId, setProductId] = useState("");
  const [qty, setQty] = useState(1);

  const orderKey = ["order", tableId];
  const { data: order, isError } = useQuery({
    queryKey: orderKey,
    queryFn: () => ordersApi.activeByTable(tableId),
    retry: false,
  });
  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.list(),
  });
  const { data: products = [] } = useQuery({
    queryKey: ["products"],
    queryFn: () => productsApi.list(),
  });

  useTablesSocket((event) => {
    if (event.data.table_id === tableId) {
      void queryClient.invalidateQueries({ queryKey: orderKey });
    }
  });

  const productName = useMemo(() => {
    const map = new Map(products.map((p) => [p.id, p.name]));
    return (id: string) => map.get(id) ?? "Producto";
  }, [products]);

  const refresh = () => queryClient.invalidateQueries({ queryKey: orderKey });

  const run = async (fn: () => Promise<unknown>) => {
    setError(null);
    try {
      await fn();
      await refresh();
    } catch (e) {
      setError(apiError(e));
    }
  };

  const openOrder = () => run(() => ordersApi.create(tableId));
  const addItem = () =>
    run(async () => {
      if (!order || !productId) return;
      await ordersApi.addItem(order.id, {
        product_id: productId,
        quantity: qty,
      });
      setQty(1);
      setProductId("");
    });
  const changeQty = (item: OrderItem, quantity: number) =>
    run(() => ordersApi.updateItem(item.id, { quantity }));
  const removeItem = (item: OrderItem) =>
    run(() => ordersApi.removeItem(item.id));
  const payItem = (item: OrderItem, quantity: number) =>
    run(() =>
      ordersApi.pay(order!.id, {
        amount: item.unit_price * quantity,
        method,
        allocations: [{ item_id: item.id, quantity }],
      }),
    );
  const payTotal = () =>
    run(() => ordersApi.pay(order!.id, { amount: order!.remaining, method }));
  const cancelPayment = (paymentId: string) =>
    run(() => paymentsApi.cancel(paymentId));
  const closeOrder = () => run(() => ordersApi.close(order!.id));
  const cancelOrder = () => run(() => ordersApi.cancel(order!.id));

  if (isError || !order) {
    return (
      <div className="flex flex-col gap-4">
        <Link
          href="/tables"
          className="inline-flex items-center gap-1 text-sm text-slate-500"
        >
          <ArrowLeft className="h-4 w-4" /> Mesas
        </Link>
        <Card>
          <CardContent className="flex flex-col items-start gap-3 p-6">
            <p className="text-slate-600">
              Esta mesa no tiene una orden activa.
            </p>
            <Button onClick={openOrder}>Abrir orden</Button>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <Link
          href="/tables"
          className="inline-flex items-center gap-1 text-sm text-slate-500"
        >
          <ArrowLeft className="h-4 w-4" /> Mesas
        </Link>
        <Badge variant={order.status}>{order.status}</Badge>
      </div>

      {error && (
        <p className="rounded bg-red-50 p-2 text-sm text-red-600">{error}</p>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Items de la orden */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Consumo</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {order.items.length === 0 && (
              <p className="text-sm text-slate-500">Sin items todavia.</p>
            )}
            {order.items.map((item) => {
              const pending = item.quantity - item.paid_quantity;
              return (
                <div
                  key={item.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-slate-100 p-3"
                >
                  <div>
                    <p className="font-medium">
                      {productName(item.product_id)}
                    </p>
                    <p className="text-sm text-slate-500">
                      {formatCOP(item.unit_price)} c/u · pagado{" "}
                      {item.paid_quantity}/{item.quantity}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => changeQty(item, item.quantity - 1)}
                      disabled={item.quantity - 1 < item.paid_quantity}
                    >
                      −
                    </Button>
                    <span className="w-8 text-center">{item.quantity}</span>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => changeQty(item, item.quantity + 1)}
                    >
                      +
                    </Button>
                    <span className="w-20 text-right font-medium">
                      {formatCOP(item.total_price)}
                    </span>
<Button
                      variant="default"
                      size="sm"
                      disabled={pending <= 0}
                      onClick={() => payItem(item, pending)}
                    >
                      Abonar {pending}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeItem(item)}
                      disabled={item.paid_quantity > 0}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              );
            })}

            {/* Agregar item */}
            <div className="mt-2 flex flex-wrap items-end gap-2 border-t border-slate-100 pt-3">
              <div className="flex flex-col gap-1">
                <Label>Producto</Label>
                <Select
                  value={productId}
                  onChange={(e) => setProductId(e.target.value)}
                >
                  <option value="">Elegir producto...</option>
                  {categories.map((cat) => (
                    <optgroup key={cat.id} label={cat.name}>
                      {products
                        .filter((p) => p.category_id === cat.id && p.is_active)
                        .map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name} — {formatCOP(p.price)}
                          </option>
                        ))}
                    </optgroup>
                  ))}
                </Select>
              </div>
              <div className="flex w-20 flex-col gap-1">
                <Label>Cant.</Label>
                <Input
                  type="number"
                  min={1}
                  value={qty}
                  onChange={(e) => setQty(Math.max(1, Number(e.target.value)))}
                />
              </div>
              <Button onClick={addItem} disabled={!productId}>
                <Plus className="h-4 w-4" /> Agregar
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Resumen y pagos */}
        <Card>
          <CardHeader>
            <CardTitle>Cierre</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <dl className="flex flex-col gap-1 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Total</dt>
                <dd className="font-medium">{formatCOP(order.total_amount)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Pagado</dt>
                <dd className="font-medium">{formatCOP(order.amount_paid)}</dd>
              </div>
              <div className="flex justify-between border-t border-slate-100 pt-1">
                <dt className="font-medium">Pendiente</dt>
                <dd className="font-semibold">{formatCOP(order.remaining)}</dd>
              </div>
            </dl>

            <div className="flex flex-col gap-1">
              <Label>Metodo de pago</Label>
              <Select
                value={method}
                onChange={(e) => setMethod(e.target.value as PaymentMethod)}
              >
                <option value="cash">Efectivo</option>
                <option value="nequi">Nequi</option>
                <option value="transfer">Transferencia</option>
              </Select>
            </div>

            <Button onClick={payTotal} disabled={order.remaining <= 0}>
              Pagar total ({formatCOP(order.remaining)})
            </Button>

            {order.status === "open" && (
              <Button
                variant="outline"
                onClick={closeOrder}
                disabled={order.items.length === 0}
              >
                Cerrar orden
              </Button>
            )}
            {(order.status === "open" || order.status === "closed") && (
              <Button variant="destructive" onClick={cancelOrder}>
                Cancelar orden
              </Button>
            )}

            {order.payments.length > 0 && (
              <div className="flex flex-col gap-2 border-t border-slate-100 pt-3">
                <p className="text-sm font-medium">Pagos</p>
                {order.payments.map((payment) => (
                  <div
                    key={payment.id}
                    className="flex items-center justify-between text-sm"
                  >
                    <span>
                      {formatCOP(payment.amount)} · {payment.method}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => cancelPayment(payment.id)}
                    >
                      Cancelar
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
