// Cliente HTTP delgada sobre axios. Todas las rutas pasan por el proxy de Next
// (`/api/*` -> backend), asi la cookie HttpOnly viaja en el mismo origen.
import axios, { type AxiosError } from "axios";

import type {
  BarTable,
  Category,
  DailyReport,
  Order,
  OrderItem,
  OrderPaymentInput,
  Payment,
  Product,
  TokenResponse,
  User,
} from "@/lib/types";

export const http = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
});

// Sesion expirada: los endpoints protegidos responden 401. Se avisa a la app
// (Providers escucha el evento) para limpiar el estado y volver al login.
http.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const url = error.config?.url ?? "";
    const isLogin = url.includes("/auth/token");
    if (
      error.response?.status === 401 &&
      !isLogin &&
      typeof window !== "undefined" &&
      window.location.pathname !== "/login"
    ) {
      window.dispatchEvent(new Event("posbar:unauthorized"));
    }
    return Promise.reject(error);
  },
);

export function apiError(error: unknown): string {
  const err = error as AxiosError<{ detail?: string; error?: string }>;
  return (
    err.response?.data?.detail ??
    err.response?.data?.error ??
    err.message ??
    "Error inesperado"
  );
}

// ---- Auth ----
export const authApi = {
  login: (email: string, password: string) =>
    http
      .post<TokenResponse>("/auth/token", { email, password })
      .then((r) => r.data),
  logout: () => http.post("/auth/logout").then(() => undefined),
  me: () => http.get<User>("/auth/me").then((r) => r.data),
};

// ---- Catalogo ----
export const categoriesApi = {
  list: () => http.get<Category[]>("/categories").then((r) => r.data),
  create: (body: { name: string; sort_order?: number }) =>
    http.post<Category>("/categories", body).then((r) => r.data),
  update: (
    id: string,
    body: { name?: string; sort_order?: number; is_active?: boolean },
  ) => http.patch<Category>(`/categories/${id}`, body).then((r) => r.data),
  remove: (id: string) =>
    http.delete(`/categories/${id}`).then(() => undefined),
};

export const productsApi = {
  list: (categoryId?: string) =>
    http
      .get<Product[]>("/products", {
        params: categoryId ? { category_id: categoryId } : {},
      })
      .then((r) => r.data),
  create: (body: {
    name: string;
    category_id: string;
    price: number;
    cost?: number;
    sku?: string | null;
  }) => http.post<Product>("/products", body).then((r) => r.data),
  update: (
    id: string,
    body: {
      name?: string;
      category_id?: string;
      price?: number;
      cost?: number;
      sku?: string | null;
      is_active?: boolean;
    },
  ) => http.patch<Product>(`/products/${id}`, body).then((r) => r.data),
  remove: (id: string) => http.delete(`/products/${id}`).then(() => undefined),
};

// ---- Mesas ----
export const tablesApi = {
  list: () => http.get<BarTable[]>("/tables").then((r) => r.data),
  create: (body: { table_number: number; label?: string | null }) =>
    http.post<BarTable>("/tables", body).then((r) => r.data),
  update: (id: string, body: { label?: string | null }) =>
    http.patch<BarTable>(`/tables/${id}`, body).then((r) => r.data),
  remove: (id: string) => http.delete(`/tables/${id}`).then(() => undefined),
};

// ---- Ordenes ----
export const ordersApi = {
  activeByTable: (tableId: string) =>
    http
      .get<Order>("/orders", { params: { table_id: tableId } })
      .then((r) => r.data),
  create: (tableId: string) =>
    http.post<Order>("/orders", { table_id: tableId }).then((r) => r.data),
  close: (orderId: string) =>
    http.post<Order>(`/orders/${orderId}/close`).then((r) => r.data),
  cancel: (orderId: string) =>
    http.post<Order>(`/orders/${orderId}/cancel`).then((r) => r.data),
  addItem: (
    orderId: string,
    body: { product_id: string; quantity: number; notes?: string | null },
  ) =>
    http.post<OrderItem>(`/orders/${orderId}/items`, body).then((r) => r.data),
  updateItem: (itemId: string, body: { quantity?: number; notes?: string | null }) =>
    http.patch<OrderItem>(`/orders/items/${itemId}`, body).then((r) => r.data),
  removeItem: (itemId: string) =>
    http.delete(`/orders/items/${itemId}`).then(() => undefined),
  pay: (orderId: string, body: OrderPaymentInput) =>
    http
      .post<{ payment: Payment; order: Order; remaining: number }>(
        `/orders/${orderId}/pay`,
        body,
      )
      .then((r) => r.data),
  history: (date?: string) =>
    http
      .get<Order[]>("/orders/history", { params: date ? { date } : {} })
      .then((r) => r.data),
};

// ---- Pagos ----
export const paymentsApi = {
  cancel: (id: string) =>
    http
      .post<{
        cancelled: boolean;
        amount: number;
        order: Order;
        remaining: number;
      }>(`/payments/${id}/cancel`)
      .then((r) => r.data),
};

// ---- Reportes ----
export const reportsApi = {
  daily: (date?: string) =>
    http
      .get<DailyReport>("/reports/daily", { params: date ? { date } : {} })
      .then((r) => r.data),
};

// ---- Usuarios ----
export const usersApi = {
  list: () => http.get<User[]>("/users").then((r) => r.data),
  create: (body: {
    name: string;
    email: string;
    password: string;
    role: string;
  }) => http.post<User>("/users", body).then((r) => r.data),
  update: (
    id: string,
    body: {
      name?: string;
      email?: string;
      role?: string;
      is_active?: boolean;
      password?: string;
    },
  ) => http.patch<User>(`/users/${id}`, body).then((r) => r.data),
  remove: (id: string) => http.delete(`/users/${id}`).then(() => undefined),
};
