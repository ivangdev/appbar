"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/input";
import {
  apiError,
  categoriesApi,
  productsApi,
  tablesApi,
  usersApi,
} from "@/lib/api";
import { formatCOP } from "@/lib/utils";

type Tab = "categories" | "products" | "tables" | "users";

const tabs: { id: Tab; label: string }[] = [
  { id: "categories", label: "Categorias" },
  { id: "products", label: "Productos" },
  { id: "tables", label: "Mesas" },
  { id: "users", label: "Usuarios" },
];

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("categories");
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold">Administracion</h1>
      <div className="flex gap-1">
        {tabs.map((t) => (
          <Button
            key={t.id}
            variant={tab === t.id ? "default" : "outline"}
            size="sm"
            onClick={() => {
              setTab(t.id);
              setError(null);
            }}
          >
            {t.label}
          </Button>
        ))}
      </div>
      {error && (
        <p className="rounded bg-red-50 p-2 text-sm text-red-600">{error}</p>
      )}
      {tab === "categories" && <Categories onError={setError} />}
      {tab === "products" && <Products onError={setError} />}
      {tab === "tables" && <Tables onError={setError} />}
      {tab === "users" && <UsersTab onError={setError} />}
    </div>
  );
}

function Categories({ onError }: { onError: (e: string | null) => void }) {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const { data = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.list(),
  });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["categories"] });
  const create = useMutation({
    mutationFn: () => categoriesApi.create({ name }),
    onSuccess: () => {
      setName("");
      onError(null);
      void invalidate();
    },
    onError: (e) => onError(apiError(e)),
  });
  const remove = useMutation({
    mutationFn: (id: string) => categoriesApi.remove(id),
    onSuccess: () => {
      onError(null);
      void invalidate();
    },
    onError: (e) => onError(apiError(e)),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Categorias</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex items-end gap-2">
          <Input
            placeholder="Nombre"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Button onClick={() => create.mutate()} disabled={!name}>
            Agregar
          </Button>
        </div>
        {data.map((c) => (
          <div
            key={c.id}
            className="flex items-center justify-between border-b border-slate-100 py-1.5"
          >
            <span>{c.name}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => remove.mutate(c.id)}
            >
              Eliminar
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function Products({ onError }: { onError: (e: string | null) => void }) {
  const qc = useQueryClient();
  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.list(),
  });
  const { data: products = [] } = useQuery({
    queryKey: ["products"],
    queryFn: () => productsApi.list(),
  });
  const [form, setForm] = useState({
    name: "",
    category_id: "",
    price: "",
    cost: "",
  });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["products"] });
  const create = useMutation({
    mutationFn: () =>
      productsApi.create({
        name: form.name,
        category_id: form.category_id,
        price: Number(form.price),
        cost: form.cost ? Number(form.cost) : undefined,
      }),
    onSuccess: () => {
      setForm({ name: "", category_id: "", price: "", cost: "" });
      onError(null);
      void invalidate();
    },
    onError: (e) => onError(apiError(e)),
  });
  const remove = useMutation({
    mutationFn: (id: string) => productsApi.remove(id),
    onSuccess: () => {
      onError(null);
      void invalidate();
    },
    onError: (e) => onError(apiError(e)),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Productos</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
          <Input
            placeholder="Nombre"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <Select
            value={form.category_id}
            onChange={(e) => setForm({ ...form, category_id: e.target.value })}
          >
            <option value="">Categoria...</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
          <Input
            type="number"
            placeholder="Precio"
            value={form.price}
            onChange={(e) => setForm({ ...form, price: e.target.value })}
          />
          <Input
            type="number"
            placeholder="Costo (admin)"
            value={form.cost}
            onChange={(e) => setForm({ ...form, cost: e.target.value })}
          />
          <Button
            onClick={() => create.mutate()}
            disabled={!form.name || !form.category_id || !form.price}
          >
            Agregar
          </Button>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-slate-500">
              <th className="py-1.5">Nombre</th>
              <th className="py-1.5">Precio</th>
              <th className="py-1.5">Costo</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} className="border-b border-slate-100">
                <td className="py-1.5">{p.name}</td>
                <td className="py-1.5">{formatCOP(p.price)}</td>
                <td className="py-1.5">
                  {p.cost != null ? formatCOP(p.cost) : "—"}
                </td>
                <td className="py-1.5 text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => remove.mutate(p.id)}
                  >
                    Eliminar
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}

function Tables({ onError }: { onError: (e: string | null) => void }) {
  const qc = useQueryClient();
  const { data = [] } = useQuery({
    queryKey: ["tables"],
    queryFn: () => tablesApi.list(),
  });
  const [number, setNumber] = useState("");
  const [label, setLabel] = useState("");
  const invalidate = () => qc.invalidateQueries({ queryKey: ["tables"] });
  const create = useMutation({
    mutationFn: () =>
      tablesApi.create({ table_number: Number(number), label: label || null }),
    onSuccess: () => {
      setNumber("");
      setLabel("");
      onError(null);
      void invalidate();
    },
    onError: (e) => onError(apiError(e)),
  });
  const remove = useMutation({
    mutationFn: (id: string) => tablesApi.remove(id),
    onSuccess: () => {
      onError(null);
      void invalidate();
    },
    onError: (e) => onError(apiError(e)),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Mesas</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex items-end gap-2">
          <Input
            type="number"
            placeholder="Numero"
            value={number}
            onChange={(e) => setNumber(e.target.value)}
          />
          <Input
            placeholder="Etiqueta (opcional)"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />
          <Button onClick={() => create.mutate()} disabled={!number}>
            Agregar
          </Button>
        </div>
        {data.map((t) => (
          <div
            key={t.id}
            className="flex items-center justify-between border-b border-slate-100 py-1.5"
          >
            <span>
              Mesa {t.table_number}{" "}
              {t.label && <span className="text-slate-500">· {t.label}</span>}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => remove.mutate(t.id)}
            >
              Eliminar
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function UsersTab({ onError }: { onError: (e: string | null) => void }) {
  const qc = useQueryClient();
  const { data = [] } = useQuery({
    queryKey: ["users"],
    queryFn: () => usersApi.list(),
  });
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "waiter",
  });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["users"] });
  const create = useMutation({
    mutationFn: () => usersApi.create(form),
    onSuccess: () => {
      setForm({ name: "", email: "", password: "", role: "waiter" });
      onError(null);
      void invalidate();
    },
    onError: (e) => onError(apiError(e)),
  });
  const toggle = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      usersApi.update(id, { is_active }),
    onSuccess: () => {
      onError(null);
      void invalidate();
    },
    onError: (e) => onError(apiError(e)),
  });
  const remove = useMutation({
    mutationFn: (id: string) => usersApi.remove(id),
    onSuccess: () => {
      onError(null);
      void invalidate();
    },
    onError: (e) => onError(apiError(e)),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Usuarios</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
          <Input
            placeholder="Nombre"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <Input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <Input
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
          <Select
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
          >
            <option value="waiter">Mesero</option>
            <option value="admin">Admin</option>
          </Select>
          <Button
            onClick={() => create.mutate()}
            disabled={!form.name || !form.email || !form.password}
          >
            Agregar
          </Button>
        </div>
        {data.map((u) => (
          <div
            key={u.id}
            className="flex items-center justify-between border-b border-slate-100 py-1.5"
          >
            <span>
              {u.name}{" "}
              <span className="text-slate-500">
                · {u.email} · {u.role}
              </span>
            </span>
            <div className="flex gap-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  toggle.mutate({ id: u.id, is_active: !u.is_active })
                }
              >
                {u.is_active ? "Desactivar" : "Activar"}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => remove.mutate(u.id)}
              >
                Eliminar
              </Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
