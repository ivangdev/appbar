"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { ConfirmButton } from "@/components/confirm-button";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select } from "@/components/ui/input";
import { useTablesSocket } from "@/hooks/use-tables-socket";
import {
  apiError,
  categoriesApi,
  ordersApi,
  paymentsApi,
  productsApi,
} from "@/lib/api";
import type { Order, OrderItem, PaymentMethod } from "@/lib/types";
import { formatCOP } from "@/lib/utils";

const METHOD_LABELS: Record<string, string> = {
  cash: "Efectivo",
  nequi: "Nequi",
  transfer: "Transferencia",
};

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString("es-CO", {
    timeZone: "America/Bogota",
    dateStyle: "short",
    timeStyle: "short",
  });
}

/** Nota editable de una linea (se guarda al salir del campo). */
function ItemNotes({
  item,
  onSave,
}: {
  item: OrderItem;
  onSave: (notes: string | null) => Promise<void>;
}) {
  return (
    <Input
      // Remonta el input si la nota cambia en el servidor (sin efectos).
      key={item.notes ?? ""}
      defaultValue={item.notes ?? ""}
      placeholder="Nota (ej: sin hielo)"
      className="mt-1 h-7 max-w-xs text-xs"
      onBlur={(e) => {
        const next = e.currentTarget.value.trim() || null;
        if (next !== (item.notes ?? null)) void onSave(next);
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          e.currentTarget.blur();
        }
      }}
    />
  );
}

export default function OrderPage() {
  const params = useParams<{ id: string }>();
  const tableId = params.id;
  const router = useRouter();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [method, setMethod] = useState<PaymentMethod>("cash");
  const [reference, setReference] = useState("");
  const [productId, setProductId] = useState("");
  const [qty, setQty] = useState(1);
  const [notes, setNotes] = useState("");
  // Cantidad a abonar por item (por defecto, todo lo pendiente).
  const [payQty, setPayQty] = useState<Record<string, number>>({});
  // Orden pagada: se conserva en pantalla aunque ya no sea la "activa".
  const [paidOrder, setPaidOrder] = useState<Order | null>(null);

  const orderKey = ["order", tableId];
  const {
    data: activeOrder,
    isError,
    isLoading,
  } = useQuery({
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
    if (event.data.table_id !== tableId) return;
    if (event.data.status === "paid") {
      // La orden deja de ser "activa"; si la pagamos aqui ya la mostramos.
      void queryClient.invalidateQueries({ queryKey: ["tables"] });
      return;
    }
    void queryClient.invalidateQueries({ queryKey: orderKey });
  });

  const order = paidOrder ?? activeOrder;

  const productName = useMemo(() => {
    const map = new Map(products.map((p) => [p.id, p.name]));
    return (id: string) => map.get(id) ?? "Producto";
  }, [products]);

  const itemName = (itemId: string) => {
    const item = order?.items.find((i) => i.id === itemId);
    return item ? productName(item.product_id) : "Producto";
  };

  const applyOrder = (next: Order) => {
    queryClient.setQueryData(orderKey, next);
    void queryClient.invalidateQueries({ queryKey: ["tables"] });
    setPaidOrder(next.status === "paid" ? next : null);
    setPayQty({});
    setReference("");
  };

  const run = async (fn: () => Promise<unknown>) => {
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError(apiError(e));
    }
  };

  const openOrder = () =>
    run(async () => {
      const created = await ordersApi.create(tableId);
      setPaidOrder(null);
      queryClient.setQueryData(orderKey, created);
      void queryClient.invalidateQueries({ queryKey: ["tables"] });
    });

  const addItem = () =>
    run(async () => {
      if (!order || !productId) return;
      await ordersApi.addItem(order.id, {
        product_id: productId,
        quantity: qty,
        notes: notes.trim() || null,
      });
      setQty(1);
      setNotes("");
      setProductId("");
      await queryClient.invalidateQueries({ queryKey: orderKey });
    });

  const changeQty = (item: OrderItem, quantity: number) =>
    run(async () => {
      await ordersApi.updateItem(item.id, { quantity });
      await queryClient.invalidateQueries({ queryKey: orderKey });
    });

  const saveNotes = async (item: OrderItem, value: string | null) => {
    await run(async () => {
      await ordersApi.updateItem(item.id, { notes: value });
      await queryClient.invalidateQueries({ queryKey: orderKey });
    });
  };

  const removeItem = (item: OrderItem) =>
    run(async () => {
      await ordersApi.removeItem(item.id);
      await queryClient.invalidateQueries({ queryKey: orderKey });
    });

  const quantityToPay = (item: OrderItem) => {
    const pending = item.quantity - item.paid_quantity;
    return Math.min(Math.max(1, payQty[item.id] ?? pending), pending);
  };

  const payItem = (item: OrderItem, quantity: number) =>
    run(async () => {
      if (!order) return;
      const result = await ordersApi.pay(order.id, {
        amount: item.unit_price * quantity,
        method,
        reference: reference.trim() || null,
        allocations: [{ item_id: item.id, quantity }],
      });
      applyOrder(result.order);
    });

  const payTotal = () =>
    run(async () => {
      if (!order) return;
      const result = await ordersApi.pay(order.id, {
        amount: order.remaining,
        method,
        reference: reference.trim() || null,
      });
      applyOrder(result.order);
    });

  const cancelPayment = (paymentId: string) =>
    run(async () => {
      const result = await paymentsApi.cancel(paymentId);
      applyOrder(result.order);
    });

  const closeOrder = () =>
    run(async () => {
      if (!order) return;
      const closed = await ordersApi.close(order.id);
      applyOrder(closed);
    });

  const cancelOrder = () =>
    run(async () => {
      if (!order) return;
      await ordersApi.cancel(order.id);
      void queryClient.invalidateQueries({ queryKey: ["tables"] });
      await queryClient.invalidateQueries({ queryKey: orderKey });
      router.push("/tables");
    });

  if (isLoading && !order) {
    return <p className="p-4 text-sm text-slate-500">Cargando orden...</p>;
  }

  if (!order) {
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
              {isError
                ? "Esta mesa no tiene una orden activa."
                : "Abriendo la orden..."}
            </p>
            <Button onClick={openOrder}>Abrir orden</Button>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </CardContent>
        </Card>
      </div>
    );
  }

  const isPaid = order.status === "paid";
  const canEdit = order.status !== "paid" && order.status !== "cancelled";

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

      {isPaid && (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-green-200 bg-green-50 p-3">
          <p className="text-sm font-medium text-green-800">
            Orden pagada por completo. La mesa quedo libre.
          </p>
          <Button size="sm" variant="outline" onClick={() => router.push("/tables")}>
            Volver a mesas
          </Button>
        </div>
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
              const toPay = quantityToPay(item);
              return (
                <div
                  key={item.id}
                  className="flex flex-col gap-2 rounded-md border border-slate-100 p-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
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
                        disabled={!canEdit || item.quantity - 1 < item.paid_quantity}
                        aria-label="Quitar una unidad"
                      >
                        −
                      </Button>
                      <span className="w-8 text-center">{item.quantity}</span>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => changeQty(item, item.quantity + 1)}
                        disabled={!canEdit}
                        aria-label="Agregar una unidad"
                      >
                        +
                      </Button>
                      <span className="w-20 text-right font-medium">
                        {formatCOP(item.total_price)}
                      </span>
                      <ConfirmButton
                        variant="ghost"
                        size="icon"
                        title="Quitar item"
                        description={`Se quitara "${productName(item.product_id)}" de la orden.`}
                        confirmLabel="Quitar"
                        disabled={!canEdit || item.paid_quantity > 0}
                        onConfirm={() => removeItem(item)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </ConfirmButton>
                    </div>
                  </div>

                  {canEdit && (
                    <div className="flex flex-wrap items-center gap-2">
                      <Label className="text-xs text-slate-500">Cantidad a abonar</Label>
                      <Input
                        type="number"
                        min={1}
                        max={pending}
                        value={pending > 0 ? toPay : 1}
                        disabled={pending <= 0}
                        className="w-20"
                        aria-label={`Cantidad a abonar de ${productName(item.product_id)}`}
                        onChange={(e) => {
                          const next = Math.max(
                            1,
                            Math.min(pending, Number(e.target.value) || 1),
                          );
                          setPayQty((prev) => ({ ...prev, [item.id]: next }));
                        }}
                      />
                      <Button
                        size="sm"
                        disabled={pending <= 0}
                        onClick={() => payItem(item, toPay)}
                      >
                        Abonar {formatCOP(item.unit_price * toPay)}
                      </Button>
                    </div>
                  )}

                  {canEdit ? (
                    <ItemNotes
                      item={item}
                      onSave={(value) => saveNotes(item, value)}
                    />
                  ) : (
                    item.notes && (
                      <p className="text-xs text-slate-500">Nota: {item.notes}</p>
                    )
                  )}
                </div>
              );
            })}

            {/* Agregar item */}
            {canEdit && (
              <div className="mt-2 flex flex-wrap items-end gap-2 border-t border-slate-100 pt-3">
                <div className="flex flex-col gap-1">
                  <Label>Producto</Label>
                  <Select
                    value={productId}
                    onChange={(e) => setProductId(e.target.value)}
                    aria-label="Producto"
                  >
                    <option value="">Elegir producto...</option>
                    {categories
                      .filter((cat) => cat.is_active)
                      .map((cat) => (
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
                <div className="flex min-w-40 flex-1 flex-col gap-1">
                  <Label>Nota (opcional)</Label>
                  <Input
                    value={notes}
                    placeholder="Ej: sin hielo"
                    onChange={(e) => setNotes(e.target.value)}
                  />
                </div>
                <Button onClick={addItem} disabled={!productId}>
                  <Plus className="h-4 w-4" /> Agregar
                </Button>
              </div>
            )}
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

            {!isPaid && (
              <>
                <div className="flex flex-col gap-1">
                  <Label>Metodo de pago</Label>
                  <Select
                    value={method}
                    onChange={(e) => setMethod(e.target.value as PaymentMethod)}
                    aria-label="Metodo de pago"
                  >
                    <option value="cash">Efectivo</option>
                    <option value="nequi">Nequi</option>
                    <option value="transfer">Transferencia</option>
                  </Select>
                </div>
                <div className="flex flex-col gap-1">
                  <Label>Referencia (opcional)</Label>
                  <Input
                    value={reference}
                    placeholder="Ej: comprobante Nequi"
                    onChange={(e) => setReference(e.target.value)}
                  />
                </div>

                <Button onClick={payTotal} disabled={order.remaining <= 0}>
                  Pagar total ({formatCOP(order.remaining)})
                </Button>
              </>
            )}

            {order.status === "open" && (
              <Button
                variant="outline"
                onClick={closeOrder}
                disabled={order.items.length === 0}
              >
                Cerrar orden
              </Button>
            )}
            {order.status === "open" && (
              <ConfirmButton
                title="Cancelar orden"
                description="La orden se anulara y la mesa quedara libre. No se puede deshacer."
                confirmLabel="Cancelar orden"
                onConfirm={cancelOrder}
              >
                Cancelar orden
              </ConfirmButton>
            )}

            {order.payments.length > 0 && (
              <div className="flex flex-col gap-2 border-t border-slate-100 pt-3">
                <p className="text-sm font-medium">Pagos</p>
                {order.payments.map((payment) => {
                  const cancelled = payment.cancelled_at != null;
                  return (
                    <div
                      key={payment.id}
                      className="flex flex-col gap-1 rounded-md border border-slate-100 p-2 text-sm"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className={cancelled ? "text-slate-400 line-through" : ""}>
                          {formatCOP(payment.amount)} ·{" "}
                          {METHOD_LABELS[payment.method] ?? payment.method}
                        </span>
                        {cancelled ? (
                          <Badge variant="cancelled">cancelado</Badge>
                        ) : (
                          <ConfirmButton
                            variant="ghost"
                            size="sm"
                            title="Cancelar pago"
                            description="El abono se anulara y los items volveran a quedar pendientes."
                            confirmLabel="Cancelar pago"
                            onConfirm={() => cancelPayment(payment.id)}
                          >
                            Cancelar
                          </ConfirmButton>
                        )}
                      </div>
                      <p className="text-xs text-slate-400">
                        {formatDateTime(payment.payment_date)}
                        {payment.reference ? ` · ${payment.reference}` : ""}
                        {cancelled && payment.cancelled_at
                          ? ` · anulado ${formatDateTime(payment.cancelled_at)}`
                          : ""}
                      </p>
                      {payment.allocations && payment.allocations.length > 0 && (
                        <ul className="ml-4 list-disc text-xs text-slate-500">
                          {payment.allocations.map((allocation) => (
                            <li key={allocation.id}>
                              {itemName(allocation.item_id)} × {allocation.quantity} (
                              {formatCOP(allocation.amount)})
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
