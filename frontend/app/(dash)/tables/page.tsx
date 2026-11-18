"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { useTablesSocket } from "@/hooks/use-tables-socket";
import { tablesApi } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  free: "#3F51B5",
  occupied: "#E67E22",
};

export default function TablesPage() {
  const queryClient = useQueryClient();
  const { data: tables = [] } = useQuery({
    queryKey: ["tables"],
    queryFn: () => tablesApi.list(),
  });

  useTablesSocket((event) => {
    if (event.data.table_id) {
      void queryClient.invalidateQueries({ queryKey: ["tables"] });
    }
  });

  const libres = tables.filter((t) => t.status === "free").length;
  const ocupadas = tables.filter((t) => t.status === "occupied").length;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h1 className="text-lg font-semibold text-slate-700">Mesas</h1>
        <p className="text-sm text-slate-400">
          {tables.length} mesas · {libres} libres · {ocupadas} ocupadas
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {tables.map((t) => {
          const isFree = t.status === "free";
          const color = STATUS_COLORS[t.status] ?? "#9CA3AF";
          const statusLabel = isFree ? "Libre" : "Ocupada";
          return (
            <Link
              key={t.id}
              href={`/tables/${t.id}`}
              className="group relative rounded-md border border-slate-200 bg-white p-4 shadow-sm shadow-slate-100/40 transition-all hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-300"
            >
              <div className="flex items-start justify-between">
                <div className="flex flex-col">
                  <span className="text-2xl font-semibold text-slate-700">
                    {t.table_number}
                  </span>
                  <span className="text-xs text-slate-400">
                    {t.label ?? `Mesa ${t.table_number}`}
                  </span>
                </div>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 px-2 py-0.5 text-xs font-medium text-slate-600 shadow-sm">
                  <span
                    className="h-1.5 w-1.5 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  {statusLabel}
                </span>
              </div>
              <div className="mt-4 flex items-center justify-between text-sm text-slate-500 group-hover:text-slate-700">
                <span>{isFree ? "Abrir orden" : "Ver orden"}</span>
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </div>
            </Link>
          );
        })}
      </div>

      {tables.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-2 rounded-md border border-dashed border-slate-200 bg-white p-10 text-center shadow-sm">
          <p className="text-sm font-medium text-slate-700">Aún no hay mesas</p>
          <p className="text-xs text-slate-400">
            Configura las mesas desde el apartado Admin.
          </p>
        </div>
      )}
    </div>
  );
}
