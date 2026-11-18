"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ConfirmButton } from "@/components/confirm-button";
import { Badge } from "@/components/ui/badge";
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
import type { BarTable, Category, Product, User } from "@/lib/types";
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
  const [sortOrder, setSortOrder] = useState("0");
  const [editing, setEditing] = useState<Category | null>(null);
  const [draft, setDraft] = useState({ name: "", sort_order: "0" });

  const { data = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.list(),
  });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["categories"] });

  const create = useMutation({
    mutationFn: () =>
      categoriesApi.create({ name, sort_order: Number(sortOrder) || 0 }),
    onSuccess: () => {
      setName("");
      setSortOrder("0");
      onError(null);
      void invalidate();
    },
    onError: (e) => onError(apiError(e)),
  });
  const update = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: { name?: string; sort_order?: number; is_active?: boolean };
    }) => categoriesApi.update(id, body),
    onSuccess: () => {
      setEditing(null);
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
          <Input
            type="number"
            min={0}
            placeholder="Orden"
            className="w-24"
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
          />
          <Button onClick={() => create.mutate()} disabled={!name}>
            Agregar
          </Button>
        </div>

        {data.map((c) => (
          <div key={c.id} className="flex flex-col gap-2 border-b border-slate-100 py-2">
            {editing?.id === c.id ? (
              <div className="flex flex-wrap items-end gap-2">
                <Input
                  value={draft.name}
                  onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                />
                <Input
                  type="number"
                  min={0}
                  className="w-24"
                  value={draft.sort_order}
                  onChange={(e) =>
                    setDraft({ ...draft, sort_order: e.target.value })
                  }
                />
                <Button
                  size="sm"
                  onClick={() =>
                    update.mutate({
                      id: c.id,
                      body: {
                        name: draft.name,
                        sort_order: Number(draft.sort_order) || 0,
                      },
                    })
                  }
                >
                  Guardar
                </Button>
                <Button size="sm" variant="outline" onClick={() => setEditing(null)}>
                  Cancelar
                </Button>
              </div>
            ) : (
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="flex items-center gap-2">
                  {c.name}
                  <span className="text-xs text-slate-400">orden {c.sort_order}</span>
                  {!c.is_active && <Badge variant="cancelled">inactiva</Badge>}
                </span>
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEditing(c);
                      setDraft({ name: c.name, sort_order: String(c.sort_order) });
                    }}
                  >
                    Editar
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      update.mutate({ id: c.id, body: { is_active: !c.is_active } })
                    }
                  >
                    {c.is_active ? "Desactivar" : "Reactivar"}
                  </Button>
                  <ConfirmButton
                    size="sm"
                    title="Eliminar categoria"
                    description="Se ocultara del catalogo (soft-delete). Puedes reactivarla despues."
                    confirmLabel="Eliminar"
                    onConfirm={async () => {
                      await remove.mutateAsync(c.id);
                    }}
                  >
                    Eliminar
                  </ConfirmButton>
                </div>
              </div>
            )}
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
    sku: "",
  });
  const [editing, setEditing] = useState<Product | null>(null);
  const [draft, setDraft] = useState({
    name: "",
    category_id: "",
    price: "",
    cost: "",
    sku: "",
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ["products"] });
  const create = useMutation({
    mutationFn: () =>
      productsApi.create({
        name: form.name,
        category_id: form.category_id,
        price: Number(form.price),
        cost: form.cost ? Number(form.cost) : undefined,
        sku: form.sku || null,
      }),
    onSuccess: () => {
      setForm({ name: "", category_id: "", price: "", cost: "", sku: "" });
      onError(null);
      void invalidate();
    },
    onError: (e) => onError(apiError(e)),
  });
  const update = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: {
        name?: string;
        category_id?: string;
        price?: number;
        cost?: number;
        sku?: string | null;
        is_active?: boolean;
      };
    }) => productsApi.update(id, body),
    onSuccess: () => {
      setEditing(null);
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
        <div className="grid grid-cols-2 gap-2 md:grid-cols-6">
          <Input
            placeholder="Nombre"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <Select
            value={form.category_id}
            aria-label="Categoria"
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
          <Input
            placeholder="SKU"
            value={form.sku}
            onChange={(e) => setForm({ ...form, sku: e.target.value.toUpperCase() })}
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
              <th className="py-1.5">Categoria</th>
              <th className="py-1.5">Precio</th>
              <th className="py-1.5">Costo</th>
              <th className="py-1.5">SKU</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} className="border-b border-slate-100 align-top">
                {editing?.id === p.id ? (
                  <>
                    <td className="py-2">
                      <Input
                        value={draft.name}
                        onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                      />
                    </td>
                    <td className="py-2">
                      <Select
                        value={draft.category_id}
                        aria-label="Categoria"
                        onChange={(e) =>
                          setDraft({ ...draft, category_id: e.target.value })
                        }
                      >
                        {categories.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                          </option>
                        ))}
                      </Select>
                    </td>
                    <td className="py-2">
                      <Input
                        type="number"
                        value={draft.price}
                        onChange={(e) => setDraft({ ...draft, price: e.target.value })}
                      />
                    </td>
                    <td className="py-2">
                      <Input
                        type="number"
                        value={draft.cost}
                        onChange={(e) => setDraft({ ...draft, cost: e.target.value })}
                      />
                    </td>
                    <td className="py-2">
                      <Input
                        value={draft.sku}
                        onChange={(e) =>
                          setDraft({ ...draft, sku: e.target.value.toUpperCase() })
                        }
                      />
                    </td>
                    <td className="py-2 text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          size="sm"
                          onClick={() =>
                            update.mutate({
                              id: p.id,
                              body: {
                                name: draft.name,
                                category_id: draft.category_id,
                                price: Number(draft.price),
                                cost: Number(draft.cost || 0),
                                sku: draft.sku || null,
                              },
                            })
                          }
                        >
                          Guardar
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setEditing(null)}
                        >
                          Cancelar
                        </Button>
                      </div>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="py-1.5">
                      <span className="flex items-center gap-2">
                        {p.name}
                        {!p.is_active && <Badge variant="cancelled">inactivo</Badge>}
                      </span>
                    </td>
                    <td className="py-1.5 text-slate-500">
                      {categories.find((c) => c.id === p.category_id)?.name ?? "—"}
                    </td>
                    <td className="py-1.5">{formatCOP(p.price)}</td>
                    <td className="py-1.5">
                      {p.cost != null ? formatCOP(p.cost) : "—"}
                    </td>
                    <td className="py-1.5 text-slate-500">{p.sku ?? "—"}</td>
                    <td className="py-1.5 text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditing(p);
                            setDraft({
                              name: p.name,
                              category_id: p.category_id ?? "",
                              price: String(p.price),
                              cost: String(p.cost ?? 0),
                              sku: p.sku ?? "",
                            });
                          }}
                        >
                          Editar
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            update.mutate({
                              id: p.id,
                              body: { is_active: !p.is_active },
                            })
                          }
                        >
                          {p.is_active ? "Desactivar" : "Reactivar"}
                        </Button>
                        <ConfirmButton
                          size="sm"
                          title="Eliminar producto"
                          description="Se ocultara del catalogo (soft-delete). Puedes reactivarlo despues."
                          confirmLabel="Eliminar"
                          onConfirm={async () => {
                            await remove.mutateAsync(p.id);
                          }}
                        >
                          Eliminar
                        </ConfirmButton>
                      </div>
                    </td>
                  </>
                )}
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
  const [editing, setEditing] = useState<BarTable | null>(null);
  const [draftLabel, setDraftLabel] = useState("");

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
  const update = useMutation({
    mutationFn: ({ id, value }: { id: string; value: string | null }) =>
      tablesApi.update(id, { label: value }),
    onSuccess: () => {
      setEditing(null);
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
            className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 py-1.5"
          >
            {editing?.id === t.id ? (
              <div className="flex flex-1 items-center gap-2">
                <span className="text-sm">Mesa {t.table_number}</span>
                <Input
                  value={draftLabel}
                  placeholder="Etiqueta"
                  onChange={(e) => setDraftLabel(e.target.value)}
                />
                <Button
                  size="sm"
                  onClick={() =>
                    update.mutate({ id: t.id, value: draftLabel || null })
                  }
                >
                  Guardar
                </Button>
                <Button size="sm" variant="outline" onClick={() => setEditing(null)}>
                  Cancelar
                </Button>
              </div>
            ) : (
              <>
                <span>
                  Mesa {t.table_number}{" "}
                  {t.label && <span className="text-slate-500">· {t.label}</span>}
                  <Badge className="ml-2" variant={t.status}>
                    {t.status === "free" ? "libre" : "ocupada"}
                  </Badge>
                </span>
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEditing(t);
                      setDraftLabel(t.label ?? "");
                    }}
                  >
                    Editar
                  </Button>
                  <ConfirmButton
                    size="sm"
                    title="Eliminar mesa"
                    description="Solo se puede eliminar una mesa sin ordenes asociadas."
                    confirmLabel="Eliminar"
                    onConfirm={async () => {
                      await remove.mutateAsync(t.id);
                    }}
                  >
                    Eliminar
                  </ConfirmButton>
                </div>
              </>
            )}
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
  const [editing, setEditing] = useState<User | null>(null);
  const [draft, setDraft] = useState({
    name: "",
    email: "",
    role: "waiter",
    password: "",
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
  const update = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: {
        name?: string;
        email?: string;
        role?: string;
        is_active?: boolean;
        password?: string;
      };
    }) => usersApi.update(id, body),
    onSuccess: () => {
      setEditing(null);
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
            aria-label="Rol"
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
            className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 py-1.5"
          >
            {editing?.id === u.id ? (
              <div className="flex flex-1 flex-wrap items-center gap-2">
                <Input
                  className="max-w-40"
                  value={draft.name}
                  onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                />
                <Input
                  className="max-w-56"
                  type="email"
                  value={draft.email}
                  onChange={(e) => setDraft({ ...draft, email: e.target.value })}
                />
                <Select
                  className="max-w-32"
                  value={draft.role}
                  aria-label="Rol"
                  onChange={(e) => setDraft({ ...draft, role: e.target.value })}
                >
                  <option value="waiter">Mesero</option>
                  <option value="admin">Admin</option>
                </Select>
                <Input
                  className="max-w-48"
                  type="password"
                  placeholder="Nueva password (opcional)"
                  value={draft.password}
                  onChange={(e) => setDraft({ ...draft, password: e.target.value })}
                />
                <Button
                  size="sm"
                  onClick={() =>
                    update.mutate({
                      id: u.id,
                      body: {
                        name: draft.name,
                        email: draft.email,
                        role: draft.role,
                        ...(draft.password ? { password: draft.password } : {}),
                      },
                    })
                  }
                >
                  Guardar
                </Button>
                <Button size="sm" variant="outline" onClick={() => setEditing(null)}>
                  Cancelar
                </Button>
              </div>
            ) : (
              <>
                <span>
                  {u.name}{" "}
                  <span className="text-slate-500">
                    · {u.email} · {u.role}
                  </span>
                  {!u.is_active && (
                    <Badge className="ml-2" variant="cancelled">
                      inactivo
                    </Badge>
                  )}
                </span>
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEditing(u);
                      setDraft({
                        name: u.name,
                        email: u.email,
                        role: u.role,
                        password: "",
                      });
                    }}
                  >
                    Editar
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      update.mutate({ id: u.id, body: { is_active: !u.is_active } })
                    }
                  >
                    {u.is_active ? "Desactivar" : "Activar"}
                  </Button>
                  <ConfirmButton
                    size="sm"
                    title="Desactivar usuario"
                    description="El usuario no podra iniciar sesion. Puedes reactivarlo despues."
                    confirmLabel="Desactivar"
                    onConfirm={async () => {
                      await remove.mutateAsync(u.id);
                    }}
                  >
                    Eliminar
                  </ConfirmButton>
                </div>
              </>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
