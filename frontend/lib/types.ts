// Tipos del dominio derivados del contrato OpenAPI generado (fuente unica de
// verdad: specs/openapi.yaml). Regenerar con: `npm run gen:types`.
//
// No editar `lib/api-types.ts` a mano; los alias de abajo son la capa estable
// que consume la app.
import type { components } from "@/lib/api-types";

type Schemas = components["schemas"];

export type Role = Schemas["UserRead"]["role"];
export type User = Schemas["UserRead"];

export type Category = Schemas["CategoryRead"];
export type Product = Schemas["ProductRead"];

export type TableStatus = Schemas["TableRead"]["status"];
export type BarTable = Schemas["TableRead"];

export type OrderStatus = Schemas["OrderStatus"];
export type PaymentMethod = Schemas["PaymentRead"]["method"];

export type OrderItem = Schemas["OrderItemRead"];
export type Allocation = Schemas["PaymentAllocation"];
export type Payment = Schemas["PaymentRead"];
export type Order = Schemas["OrderRead"];

export type TokenResponse = Schemas["Token"];
export type OrderPaymentInput = Schemas["OrderPayment"];

export type ReportByTable = Schemas["ReportByTable"];
export type ReportByProduct = Schemas["ReportByProduct"];
export type DailyReport = Schemas["DailyReport"];

// Evento WebSocket (x-websocket en specs/openapi.yaml). El backend emite un
// unico payload de orden para todos los `order_*`/`payment_*` + el de mesa.
export interface TableEvent {
  type:
    | "table_status_update"
    | "new_order"
    | "order_updated"
    | "order_closed"
    | "order_cancelled"
    | "payment_made"
    | "payment_cancelled"
    | "order_paid";
  data: {
    order_id?: string;
    table_id: string;
    table_number: number;
    status?: OrderStatus;
    table_status?: TableStatus;
    total_amount?: number;
    amount_paid?: number;
    remaining?: number;
  };
}
